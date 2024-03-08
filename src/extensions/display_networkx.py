#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import math
import random
import re

from qtpy.QtCore import QLineF, QPointF, QRectF, QSizeF, Qt, qFuzzyCompare
from qtpy.QtGui import (
    QColor, QGuiApplication, QPainter, QPainterPath, QPen, QRadialGradient)
from qtpy.QtWidgets import (
    QCheckBox, QGraphicsItem, QGraphicsScene, QGraphicsView, QGroupBox,
    QHBoxLayout, QLineEdit, QPushButton, QStyle, QVBoxLayout, QWidget)
from traits.api import (
    Bool, Dict, Float, Instance, Int, List, String, Undefined, WeakRef)

import karabogui.icons as icons
from karabogui import messagebox
from karabogui.binding.api import VectorHashBinding, get_binding_value
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.events import KaraboEvent
from karabogui.request import (
    broadcast_event, get_scene_from_server, get_topology,
    onConfigurationUpdate, onSchemaUpdate)

from .models.api import FilterInstance, NetworkXModel, NodePosition

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
FILTER_ACTIVE_COLOR = "#d8f3dc"
FILTER_DISABLED_COLOR = "#ced4da"


try:
    PAUSE_ICON = icons.mediaPause.icon
    PLAY_ICON = icons.mediaStart.icon
    CLEAR_FILTER_ICON = icons.stop.icon
    FILTER_TRAFFIC_ICON = icons.deviceMonitored.icon
except AttributeError:
    PAUSE_ICON = icons.mediaPause
    PLAY_ICON = icons.mediaStart
    CLEAR_FILTER_ICON = icons.stop
    FILTER_TRAFFIC_ICON = icons.deviceMonitored


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
    it represents, and SHIFT clicking a node will open it in the configurator.
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

    def apply_filter(self, filters):
        """
        Apply the filters to the node. It will be invisible if none match.

        :param filters: A list of FilterItems

        """
        self_match = False or len(filters) == 0
        edge_match = False or len(filters) == 0
        visible_edges = []
        for filter in filters:
            match, edge_matches = filter.apply_filter(self)
            self_match |= match
            visible_edges += edge_matches

        edge_match |= len(visible_edges) > 0
        if self_match or edge_match:
            self.setVisible(True)
            # only show edge if a node matched the filter
            # or if there are no filters
            for edge in self.edge_list:
                if edge in visible_edges or len(filters) == 0:
                    edge.setVisible(True)
                else:
                    edge.setVisible(False)
        else:
            self.setVisible(False)
            for edge in self.edge_list:
                edge.setVisible(False)

    def mouseDoubleClickEvent(self, event):
        """
        Double click events will open the device scene

        This is mostly a copy of the topology method, except that we need
        to request schemas and configurations every time, as we will not
        have necessarily done this for a given node already.
        """
        device_id = str(self.label)

        def _config_handler():
            """Act on the arrival of the configuration"""
            scenes = proxy["availableScenes"].value
            if scenes is Undefined or not len(scenes):
                messagebox.show_warning(
                    "The device <b>{}</b> does not specify a scene "
                    "name!".format(device_id))
            else:
                scene_name = scenes[0]
                get_scene_from_server(device_id, scene_name)

        def _schema_handler():
            """Act on the arrival of the schema"""
            if proxy["availableScenes"] is None:
                messagebox.show_warning(
                    "The device <b>{}</b> does not specify a scene "
                    "name!".format(device_id))
                return
            scenes = proxy["availableScenes"].value
            if scenes is Undefined:
                onConfigurationUpdate(proxy, _config_handler, request=True)
            elif not len(scenes):
                messagebox.show_warning(
                    "The device <b>{}</b> does not specify a scene "
                    "name!".format(device_id))
            else:
                scene_name = scenes[0]
                get_scene_from_server(device_id, scene_name)

        proxy = get_topology().get_device(device_id)
        if not len(proxy.binding.value):
            # We completely miss our schema and wait for it.
            onSchemaUpdate(proxy, _schema_handler, request=True)
        elif proxy["availableScenes"].value is Undefined:
            onConfigurationUpdate(proxy, _config_handler, request=True)
        else:
            scenes = proxy["availableScenes"].value
            if not len(scenes):
                # The device might not have a scene name in property
                messagebox.show_warning(
                    "The device <b>{}</b> does not specify a scene "
                    "name!".format(device_id))
            else:
                scene_name = scenes[0]
                get_scene_from_server(device_id, scene_name)

    def mousePressEvent(self, event):
        """
        A SHIFT-click will show the device in the configurator.

        Cannot use ALT because that event is caught by the scene-view
        itself already and it will not even forward the mouse event if
        the ALT modifier is pressed.
        """
        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier:
            broadcast_event(KaraboEvent.ShowConfiguration,
                            {'proxy': get_topology().get_device(self.label)})
            event.accept()
            return

        self.update()


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
            self.timer_id = self.startTimer(1000 // 25)
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
                self.timer_id = self.startTimer(1000 // 25)

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

    def filter(self, filters):
        """
        Apply a list of filters to all nodes on the scene

        :param filters: A list of FilterItems
        """
        for node in self.scene().items():
            if not isinstance(node, Node):
                continue
            node.apply_filter(filters)


class FilterItem(QCheckBox):
    """
    Filter items determine which nodes (and connecting edges) are shown.

    Filters usually OR, and can be enabled and disabled.
    """

    def __init__(self, filter_text, parent_layout, main_widget,
                 active=True, parent=None):
        super().__init__(parent=parent)
        self.setText(filter_text)
        self.set_button_style(active)
        self.clicked.connect(self.toggle_active)
        self.parent_layout = parent_layout
        self.main_widget = main_widget
        self.is_active = active
        self.setMaximumWidth(100)

    def set_button_style(self, active):
        if active:
            self.setStyleSheet(
                f"QCheckBox {{background-color: {FILTER_ACTIVE_COLOR};}}")
        else:
            self.setStyleSheet(
                f"QCheckBox {{background-color: {FILTER_DISABLED_COLOR};}}")
        self.setChecked(active)

    def toggle_active(self):
        """
        Toggle the filters active state. Only active filters are applied.
        """
        self.is_active = not self.is_active
        self.set_button_style(self.is_active)
        self.main_widget.update_filter()

    def apply_filter(self, node):
        """
        Evaluate the filter for the node.

        :param node: a Node object

        :return: A tuple (Bool, List) where the bool indicates if the Node
            evaluates against the filter, and the list contains those
            edges which are determined to be visible by the filter.
        """
        match = False
        edge_matches = []
        filter_text = self.text()
        if re.match(f".*{filter_text}.*", node.label):
            match = True
        for edge in node.edge_list:
            if re.match(f".*{filter_text}.*", edge.source.label):
                edge_matches.append(edge)
            elif re.match(f".*{filter_text}.*", edge.dest.label):
                edge_matches.append(edge)
        return match, edge_matches

    def active(self):
        return self.is_active

    def mouseDoubleClickEvent(self, event):
        self.parent_layout.removeWidget(self)
        self.main_widget.update_filter()
        self.deleteLater()


class FilterLineEdit(QLineEdit):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText("Add filter here...")

    def focusInEvent(self, event):
        self.clear()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.setText("Add filter here...")
        super().focusInEvent(event)


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
    filter_ledit = Instance(QLineEdit)
    filter_instances = Instance(QHBoxLayout)

    def create_widget(self, parent):
        widget = QWidget(parent=parent)
        layout = QVBoxLayout()

        # add the filter tool bar
        filter_layout = QHBoxLayout()
        self.filter_ledit = FilterLineEdit()
        self.filter_ledit.returnPressed.connect(self.on_filter)
        clear_filter_btn = QPushButton()
        clear_filter_btn.setIcon(CLEAR_FILTER_ICON)
        clear_filter_btn.clicked.connect(self.on_clear_filter)
        freeze_btn = QPushButton()
        freeze_btn.setIcon(PAUSE_ICON)
        freeze_btn.clicked.connect(self.on_freeze)
        self.freeze_btn = freeze_btn
        self.frozen = False
        filter_layout.addWidget(self.filter_ledit)
        filter_layout.addWidget(clear_filter_btn)
        filter_layout.addWidget(freeze_btn)
        layout.addLayout(filter_layout)

        self.filter_instances = QHBoxLayout()
        # add a stretch of align right
        self.filter_instances.addStretch()
        # and then any saved filters
        for instance in self.model.filterInstances:
            filter_widget = FilterItem(instance.filter_text,
                                       self.filter_instances,
                                       main_widget=self,
                                       active=instance.is_active,
                                       parent=self.widget)
            self.filter_instances.addWidget(
                filter_widget, 0, Qt.AlignRight)
        group_box = QGroupBox("Currently Configured Filters")
        group_box.setStyleSheet("""
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center; /* position at the top center */
            margin-top: 2ex;
            }
        """)
        group_box.setLayout(self.filter_instances)
        layout.addWidget(group_box)

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
            self.update_filter()

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

    def on_filter(self):
        """
        Adds a filter item, when the user hits enter
        """
        filter_text = self.filter_ledit.text()
        for idx in range(self.filter_instances.count()):
            item = self.filter_instances.itemAt(idx).widget()
            if item and item.text() == filter_text:
                return  # don't add twice
        filter_widget = FilterItem(filter_text, self.filter_instances,
                                   main_widget=self,
                                   parent=self.widget)
        self.filter_instances.addWidget(
            filter_widget, 0, Qt.AlignRight)
        self.update_filter()

    def update_filter(self):
        """
        Updates and applies the filters acting on the nodes
        """
        filters = []
        filter_instances = []
        for idx in range(self.filter_instances.count()):
            item = self.filter_instances.itemAt(idx).widget()
            if item:
                if item.active():
                    filters.append(item)
                # save state for model
                traits = {"filter_text": item.text(),
                          "is_active": item.active()}
                filter_instances.append(FilterInstance(**traits))
        # we save the activation state to the model.
        self.model.filterInstances = filter_instances
        self.graphwidget.filter(filters)

    def on_clear_filter(self):
        """
        Clears all filters and restores the traffic filter as a default filter
        """
        while self.filter_instances.count():
            widget = self.filter_instances.itemAt(0).widget()
            self.filter_instances.removeWidget(
                self.filter_instances.itemAt(0).widget())
            if widget:
                widget.deleteLater()
        # add a stretch again
        self.filter_instances.addStretch()
        self.update_filter()
