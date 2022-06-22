#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import math
import random

from qtpy.QtCore import QLineF, QPointF, QRectF, QSizeF, Qt, qFuzzyCompare
from qtpy.QtGui import QColor, QPainter, QPainterPath, QPen, QRadialGradient
from qtpy.QtWidgets import (
    QGraphicsItem, QGraphicsScene, QGraphicsView, QPushButton, QStyle,
    QVBoxLayout, QWidget)
from traits.api import Bool, Dict, Float, Instance, Int, List, String, WeakRef

import karabogui.icons as icons
from karabogui.binding.api import VectorHashBinding, get_binding_value
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)

from .models.api import NetworkXModel, NodePosition

GROUP_COLORS = {
    "p2p": (QColor("#52b788"), QColor("#6c757d")),
    "daq_sink": (QColor("#ffc8dd"), QColor("#7209b7")),
    "daq_source": (QColor("#bde0fe"), QColor("#7209b7")),
    "ERROR": (QColor("#ffadad"), QColor("#6c757d"))
}

STATUS_COLOR = {
    "active": QColor("#52b788"),
    "passive": QColor("#9a8c98"),
    "output_broken": QColor("#e76f51"),
    "input_broken": QColor("#e76f51"),
    "unclear": QColor("#f4a261")
}

SHADOW_COLOR = QColor(100, 100, 100, 100)

try:
    PAUSE_ICON = icons.mediaPause.icon
    PLAY_ICON = icons.mediaStart.icon
except AttributeError:
    PAUSE_ICON = icons.mediaPause
    PLAY_ICON = icons.mediaStart


class Edge:
    pass  # forward definition


# adapted from
# https://doc.qt.io/qt-5/qtwidgets-graphicsview-elasticnodes-example.html
class Node(QGraphicsItem):
    """
    The Nodes in the Graph.

    Nodes can have different types and are defined by the edges connecting
    them to other nodes.

    Nodes allow filters to be applied to them which influence their visibility.

    Finally, double-clicking a node will open the device scene of the device
    it represents, and CTRL clicking a node will open it in the configurator.
    """
    edge_list = List(Edge)
    new_pos = Instance(QPointF)
    graph = WeakRef(QWidget)
    group = String()
    label = String()
    node_scale = Float()

    def __init__(self, graphWidget, label, group):
        super().__init__()
        flags = QGraphicsItem
        self.setFlag(flags.ItemIsMovable, True)
        self.setFlag(flags.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self.setZValue(1.0)
        self.node_scale = 1.0
        self.edge_list = []
        self.graph = graphWidget
        self.label = label
        self.group = group
        self.setToolTip(self.label)

    def add_edge(self, edge):
        self.edge_list.append(edge)
        edge.adjust()

    def edges(self):
        return self.edge_list

    def calculate_forces(self):
        if not self.scene() or self.scene().mouseGrabberItem() == self:
            self.new_pos = self.pos()
            return

        xvel = 0
        yvel = 0
        items = self.scene().items()
        for node in items:
            if not isinstance(node, Node):
                continue  # skip items that are note a Node
            vec = self.mapToItem(node, 0, 0)
            dx = vec.x()
            dy = vec.y()
            length = 2.0 * (dx ** 2 + dy ** 2)
            if length > 20000:
                continue
            if length > 0:
                xvel += dx * 100. / length
                yvel += dy * 100. / length

        weight = (len(self.edge_list) + 1) * 10
        for edge in self.edge_list:
            if edge.source_node() == self:
                vec = self.mapToItem(edge.dest_node(), 0, 0)
            else:
                vec = self.mapToItem(edge.source_node(), 0, 0)
            xvel -= vec.x() / weight
            yvel -= vec.y() / weight

        if abs(xvel) < 0.3 and abs(yvel) < 0.3:
            xvel = yvel = 0

        scene_rect = self.scene().sceneRect()
        self.new_pos = self.pos() + QPointF(xvel, yvel)
        self.new_pos.setX(min(max(self.new_pos.x(), scene_rect.left() + 10),
                              scene_rect.right() - 10))
        self.new_pos.setY(min(max(self.new_pos.y(), scene_rect.top() + 10),
                              scene_rect.bottom() - 10))

    def advance_position(self):
        if self.new_pos == self.pos():
            return False
        self.setPos(self.new_pos)
        return True

    def boundingRect(self):
        adjust = 2.0
        scl = self.node_scale
        return QRectF(-10 * scl - adjust, -10 * scl - adjust,
                      20 * scl + 3 + adjust, 20 * scl + 3 + adjust)

    def shape(self):
        path = QPainterPath()
        scl = self.node_scale
        path.addEllipse(-10 * scl, -10 * scl, 20 * scl, 20 * scl)
        return path

    def paint(self, painter, option, widget=None):
        scl = self.node_scale
        painter.setPen(Qt.NoPen)
        painter.setBrush(SHADOW_COLOR)
        painter.drawEllipse(-10 * scl + 3, -10 * scl + 3, 20 * scl, 20 * scl)
        gradient = QRadialGradient(-3 * scl, -3 * scl, 10 * scl)
        color1, color2 = GROUP_COLORS[self.group]
        pencolor = QColor("black")

        if option.state == QStyle.State_Sunken:
            gradient.setCenter(3 * scl, 3 * scl)
            gradient.setFocalPoint(3 * scl, 3 * scl)
            gradient.setColorAt(1, color1.lighter(120))
            gradient.setColorAt(0, color2.lighter(120))
        else:
            gradient.setColorAt(0, color1)
            gradient.setColorAt(1, color2)
        painter.setBrush(gradient)
        painter.setPen(QPen(pencolor, 0))
        painter.drawEllipse(-10 * scl, -10 * scl, 20 * scl, 20 * scl)
        font = painter.font()
        font.setBold(False)
        font.setPointSize(2)
        painter.setFont(font)
        painter.drawText(self.boundingRect(), self.label)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edge_list:
                edge.adjust()
            self.graph.itemMoved()

        return super().itemChange(change, value)


class Edge(QGraphicsItem):
    """
    Edges define the connections between Nodes.

    Here, edges are the p2p connection between devices. They are classified
    by whether a connection is active, passive or broken, and what rate
    is currently transferred through it.
    """
    source = WeakRef(Node)
    dest = WeakRef(Node)
    source_point = Instance(QPointF)
    dest_point = Instance(QPointF)
    status = String()

    def __init__(self, source_node, dest_node, status):
        super().__init__()
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1.0)
        self.source = source_node
        self.dest = dest_node
        self.status = status
        self.source.add_edge(self)
        self.dest.add_edge(self)
        self.adjust()

    def source_node(self):
        return self.source

    def dest_node(self):
        return self.dest

    def adjust(self):
        if self.source is None or self.dest is None:
            return

        line = QLineF(self.mapFromItem(self.source, 0, 0),
                      self.mapFromItem(self.dest, 0, 0))
        length = line.length()
        self.prepareGeometryChange()
        if length > 20:
            edge_offset = QPointF(line.dx() * 10 / length,
                                  line.dy() * 10 / length)
            self.source_point = line.p1() + edge_offset
            self.dest_point = line.p2() - edge_offset
        else:
            self.source_point = self.dest_point = line.p1()

    def boundingRect(self):
        if self.source is None or self.dest is None:
            return QRectF()

        size = QSizeF(self.dest_point.x() - self.source_point.x(),
                      self.dest_point.y() - self.source_point.y())
        rect = QRectF(self.source_point, size)
        rect.normalized()

        return rect

    def paint(self, painter, option, widget=None):
        if self.source is None or self.dest is None:
            return
        line = QLineF(self.source_point, self.dest_point)
        if qFuzzyCompare(line.length(), 0):
            return

        color = STATUS_COLOR[self.status]

        painter.setPen(
            QPen(color,
                 5,
                 Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)


class NetworkX:
    pass  # forward definition


class GraphWidget(QGraphicsView):
    """
    The GraphWidget is the main Canvas to render Nodes and Edges on.

    It can be zoomed in and out of.
    """
    _scene = WeakRef(QGraphicsScene)
    timer_id = Int()
    main_widget = WeakRef(NetworkX)
    scale_factor = Float()
    nodes = Dict(String, Node)
    edges = Dict(String, Dict(String, Edge))

    def __init__(self, main_widget, parent=None):
        super().__init__(parent=parent)
        self.scale_factor = 1.0
        self.main_widget = main_widget
        self._scene = QGraphicsScene(parent=self)
        self._scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self._scene.setSceneRect(-400 * 2, -400 * 2, 800 * 2, 800 * 2)
        self.setScene(self._scene)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(
            QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(
            QGraphicsView.AnchorUnderMouse)
        self.scale(0.8, 0.8)
        self.setMinimumSize(800, 800)
        self.timer_id = 0
        self.nodes = {}
        self.edges = {}

    def create_graph(self, node_edge_list):
        """
        Create or update a graph

        :param node_edge_list: A list of Hashes defining nodes and edges

        Updates will only happen if nodes are not present yet, or if the
        byte rate of an edge has changed.
        """

        # first pass is for the nodes themselves
        nodes = self.nodes
        edges = self.edges
        for row in node_edge_list:
            source = row["originNode"]
            dest = row["destinationNode"]
            source_type = row["originType"]
            dest_type = row["destinationType"]
            status = row["status"]
            origin_pos = row["originPos"]
            dest_pos = row["destPos"]
            if source not in nodes:
                source_node = Node(self, label=source, group=source_type)
                self._scene.addItem(source_node)
                source_node.setPos(*origin_pos)
                nodes[source] = source_node
            else:
                source_node = nodes[source]
                # daq types have priority
                if "daq" in source_type:
                    if source_node.group != "daq_sink":
                        source_node.group = source_type

            if dest not in nodes:
                dest_node = Node(self, label=dest, group=dest_type)
                self._scene.addItem(dest_node)
                dest_node.setPos(*dest_pos)
                nodes[dest] = dest_node
            else:
                dest_node = nodes[dest]
                # daq types have priority
                if "daq" in dest_type:
                    if dest_node.group != "daq_sink":
                        dest_node.group = dest_type

            if source not in edges or dest not in edges[source]:
                edge = Edge(source_node, dest_node, status=status)
                self._scene.addItem(edge)
                sedge = edges.setdefault(source, {})
                sedge[dest] = edge

        self.nodes = nodes
        self.edges = edges

    def itemMoved(self):
        if self.timer_id == 0:
            self.timer_id = self.startTimer(1000.0 / 25)
            self.main_widget.toggle_freeze_button(True)

    def timerEvent(self, event):
        nodes = []
        items = self.scene().items()
        for node in items:
            if not isinstance(node, Node):
                continue
            nodes.append(node)

        for node in nodes:
            node.calculate_forces()

        items_moved = False
        for node in nodes:
            if node.advance_position():
                items_moved = True

        if not items_moved:
            self.killTimer(self.timer_id)
            self.timer_id = 0
            self.save_node_positions()

    def freeze(self, freeze):
        """
        Freeze any current motion or enable it again

        :param freeze: True to freeze motion, False to enable
        """
        if freeze:
            self.killTimer(self.timer_id)
            self.timer_id = 0
            self.save_node_positions()
        else:
            if self.timer_id == 0:
                self.timer_id = self.startTimer(1000.0 / 25)

    def save_node_positions(self):
        """
        Trigger saving node positions in the widgets model
        """
        node_positions = {}
        items = self.scene().items()
        for node in items:
            if not isinstance(node, Node):
                continue
            node_positions[node.label] = [node.pos().x(), node.pos().y()]
        self.main_widget.save_node_positions(node_positions)

    def wheelEvent(self, event):
        self.scale_view(math.pow(2., -event.angleDelta().y() / 240))

    def scale_view(self, scale_factor):
        factor = self.transform().scale(scale_factor, scale_factor)
        factor = factor.mapRect(QRectF(0, 0, 1, 1)).width()
        if factor < 0.07 or factor > 100:
            return
        self.scale_factor = factor
        self.scale(scale_factor, scale_factor)


@register_binding_controller(
    ui_name='NetworkX Graph',
    binding_type=VectorHashBinding,
    klassname='NetworkX',
    is_compatible=with_display_type("NetworkX"),
    priority=-10, can_show_nothing=False, can_edit=False)
class NetworkX(BaseBindingController):
    """A NetworkX graph for p2p channels and device hiearchies"""
    model = Instance(NetworkXModel, args=())
    graphwidget = WeakRef(GraphWidget)
    freeze_btn = Instance(QPushButton)
    frozen = Bool()

    def create_widget(self, parent):
        widget = QWidget(parent=parent)
        layout = QVBoxLayout()
        freeze_btn = QPushButton()
        freeze_btn.setIcon(PAUSE_ICON)
        freeze_btn.clicked.connect(self.on_freeze)
        self.freeze_btn = freeze_btn
        self.frozen = False
        layout.addWidget(freeze_btn)
        self.graphwidget = GraphWidget(self, parent=widget)
        layout.addWidget(self.graphwidget)
        widget.setLayout(layout)
        return widget

    def value_update(self, proxy):
        value = get_binding_value(proxy)
        if value is None:
            return

        node_edge_list = []
        any_random_pos = False
        position_dict = {p.device_id: (p.x, p.y)
                         for p in self.model.nodePositions}
        for row in value:
            origin = row["originNode"]
            dest = row["destinationNode"]
            if origin not in position_dict:
                any_random_pos |= True

            if dest not in position_dict:
                any_random_pos |= True

            # in case the node is not saved with its position yet, we generate
            # a random start position
            origin_pos = position_dict.get(
                origin, [(random.random() - 0.5) * 100,
                         (random.random() - 0.5) * 100])
            des_pos = position_dict.get(
                dest, [(random.random() - 0.5) * 100,
                       (random.random() - 0.5) * 100])
            row["originPos"] = origin_pos
            row["destPos"] = des_pos
            row["originNode"] = origin
            row["destinationNode"] = dest
            node_edge_list.append(row)
        if self.graphwidget:
            self.graphwidget.create_graph(node_edge_list)

        # sort out if any new nodes (with random positions) were added
        # if so, we should un-freeze the widget so that forces are applied
        # and bring it into a new equilibrium.
        if not any_random_pos:
            self.graphwidget.freeze(True)
            self.toggle_freeze_button(True)
            self.frozen = True
        # if nothing was added we maintain the existing positions.
        else:
            self.toggle_freeze_button(False)
            self.frozen = False

    def save_node_positions(self, node_positions):
        """
        Saves node positions to the model
        """
        position_list = []
        for device_id, (x, y) in node_positions.items():
            traits = {'device_id': device_id, 'x': x, 'y': y}
            position_list.append(NodePosition(**traits))
        self.model.nodePositions = position_list

    def on_freeze(self):
        """
        If the canvas is frozen, ensure that the toggle button reflects this.
        """
        if self.frozen:
            self.graphwidget.freeze(False)
            self.toggle_freeze_button(False)
            self.frozen = False
        else:
            self.graphwidget.freeze(True)
            self.toggle_freeze_button(True)
            self.frozen = True

    def toggle_freeze_button(self, freeze):
        """
        Toggle the freeze button between its two icons.
        """
        if freeze and self.freeze_btn.icon() != PAUSE_ICON:
            self.freeze_btn.setIcon(PAUSE_ICON)
        elif self.freeze_btn.icon() != PLAY_ICON:
            self.freeze_btn.setIcon(PLAY_ICON)
