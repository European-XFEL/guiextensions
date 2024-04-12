#############################################################################
# Created on Jan 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import QEvent, QPoint, QRectF, QSize, Qt, Signal, Slot
from qtpy.QtGui import QBrush, QColor, QPixmap
from qtpy.QtWidgets import (
    QAction, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QVBoxLayout,
    QWidget)
from traits.api import Instance, WeakRef

from karabogui.api import (
    BaseBindingController, StringBinding, get_binding_value, icons,
    register_binding_controller, with_display_type)

from .models.api import Base64ImageModel

try:
    from karabo.common.scenemodel.api import extract_base64image
except ImportError:
    from karabo.common.scenemodel.api import (
        convert_from_svg_image as extract_base64image)

try:
    from karabogui.api import ToolBar
except ImportError:
    from karabogui.widgets.toolbar import ToolBar

from enum import Enum


class MouseMode(Enum):
    Zoom = 1
    Move = 2
    Pointer = 3


class PixmapView(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(parent=self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem(QPixmap())
        self.scene.addItem(self.pixmap_item)
        self.fitInView(self.scene.sceneRect())

    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)
        rect = self.scene.sceneRect()
        self.fitInView(rect)
        self.view_rect = rect

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.scene.sceneRect()
        self.fitInView(rect)
        self.view_rect = rect


class KaraboImagePixMap(QWidget):
    escapeKeyPressed = Signal()

    def __init__(self, parent=None):
        """
        Initialize the KaraboImagePixMap.

        Args:
        - parent: Parent widget.
        """
        super().__init__(parent)
        self.view_rect = None
        self.start_pos = None
        self.temp_zoom_rect = None
        self.zoom_image = None
        self.scene_zoomed_region = None
        self.pixmap = None
        self.mouse_mode = None
        self.zoom_enabled = False
        self.last_mouse_pos = None
        self.zoom_factor = 1

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Connect ESC key press event
        self.setFocusPolicy(Qt.StrongFocus)
        # self.keyPressEvent = self.key_press_event_handler

        zoom_toolbar = self._create_toolbar(parent)
        self.layout().addWidget(zoom_toolbar)

        self.view = PixmapView(parent=self)
        self.layout().addWidget(self.view)
        layout.setStretch(0, 1)

        self.view.viewport().installEventFilter(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.pointer_action.trigger()

    def deselect_current_button(self):
        self.pointer_action.setCheckable(True)
        self.zoom_in_action.setCheckable(False)
        self.move_action.setCheckable(False)

    def eventFilter(self, obj, event):
        if obj == self.view.viewport():
            if event.type() == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
            elif event.type() == QEvent.MouseMove:
                self.mouseMoveEvent(event)
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
        return super().eventFilter(obj, event)

    def zoom_out(self):
        """
        Zoom out the view to display the entire original image.

        This method resets the scene rectangle to match the original
        image size and adjusts the view to fit the scene.
        If the mouse mode is set to 'Move', it also centers the image
        within the view.

        """
        pixmap_rect = self.view.pixmap_item.pixmap().rect()
        pixmap_rect_f = QRectF(pixmap_rect)
        self.view.scene.setSceneRect(pixmap_rect_f)

        self.view.fitInView(self.view.scene.sceneRect())

        if self.mouse_mode == MouseMode.Move:
            if self.zoom_enabled:
                pixmap_rect = self.view.pixmap_item.pixmap().rect()
                pixmap_rect_f = QRectF(pixmap_rect)
                self.view.scene.setSceneRect(pixmap_rect_f)
            self.move_center()

    def move_center(self):
        # Center the image in the view
        view_rect = self.view.viewport().rect()
        scene_rect = self.view.mapToScene(view_rect).boundingRect()
        image_rect = self.view.pixmap_item.mapRectToScene(
            self.view.pixmap_item.boundingRect())
        # Calculate the center offset to center the image within the view
        center_offset = (scene_rect.center() -
                         image_rect.center()).toPoint()
        self.view.pixmap_item.setPos(
            self.view.pixmap_item.pos() + center_offset)
        self.view.fitInView(self.view.scene.sceneRect())

    def zoom_in(self, zoom_region):
        # Convert the rect to scene coordinates
        self.scene_zoomed_region = QRectF(
            self.view.mapToScene(zoom_region.topLeft()),
            self.view.mapToScene(zoom_region.bottomRight()))
        # Set the scene rectangle to match the zoomed region
        self.view.scene.setSceneRect(self.scene_zoomed_region)

        # Set the pixmap item to display the cropped pixmap
        self.view.pixmap_item.setPixmap(self.view.pixmap_item.pixmap())
        self.view.fitInView(self.view.scene.sceneRect())

    def mousePressEvent(self, event):
        """
        Handle mouse move events.

        Notes:
            - If in 'Zoom' mode and zoom enabled:
                - Draws the final yellow rectangle to
                indicate the area to zoom.
            - If in 'Move' mode:
                - Tracks the mouse position upon clicking.
            - Otherwise, zooms out.
        """
        if self.mouse_mode == MouseMode.Zoom:
            if (event.button() in (Qt.LeftButton, Qt.MiddleButton)
               and not self.zoom_enabled):
                self.start_pos = event.pos()
                brush_color = QColor(Qt.yellow)
                brush_color.setAlphaF(0.25)
                brush = QBrush(brush_color)
                self.temp_zoom_rect = self.view.scene.addRect(
                    0, 0, 0, 0, pen=Qt.yellow, brush=brush)
                self.zoom_enabled = True
        elif self.mouse_mode == MouseMode.Move:
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        Notes:
            - If in 'Zoom' mode and zoom enabled:
                - Draws a yellow rectangle representing the area to zoom.
            - If in 'Move' mode:
                - Moves the zoomed image if zoomed out or left button pressed.
            - Otherwise, zooms out.
        """
        if self.mouse_mode == MouseMode.Zoom and self.zoom_enabled:
            end_pos = event.pos()
            start_point_scene = self.view.mapToScene(self.start_pos)
            end_point_scene = self.view.mapToScene(end_pos)
            self.zoom_image = QRectF(
                start_point_scene, end_point_scene).normalized()
            self.temp_zoom_rect.setRect(self.zoom_image)

        elif (self.mouse_mode == MouseMode.Move and
              (event.buttons() in (Qt.MiddleButton, Qt.LeftButton))):
            if self.last_mouse_pos is not None:
                delta = event.pos() - self.last_mouse_pos
                new_pos = (
                    self.view.pixmap_item.pos() + self.view.mapToScene(delta) -
                    self.view.mapToScene(QPoint(0, 0)))
                self.view.pixmap_item.setPos(new_pos)
            self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release event.

        Args:
        - event: QMouseEvent object representing the mouse release event.
        """
        if self.mouse_mode == MouseMode.Zoom:
            if (event.button() in (Qt.LeftButton, Qt.MiddleButton)
                    and self.zoom_image):
                rect_in_scene = self.zoom_image.intersected(self.view_rect)
                zoom_region = self.view.mapFromScene(
                    rect_in_scene).boundingRect()
                self.zoom_in(zoom_region)

                if self.temp_zoom_rect:
                    self.view.scene.removeItem(self.temp_zoom_rect)
                    self.temp_zoom_rect = None
                    self.start_pos = None
                self.zoom_image = None
            elif event.button() in (Qt.RightButton, Qt.MidButton):
                self.zoom_out()
            self.zoom_enabled = False
        elif self.mouse_mode == MouseMode.Move:
            self.last_mouse_pos = None
            if event.button() == Qt.RightButton:
                self.zoom_out()
        elif self.mouse_mode == MouseMode.Pointer:
            self.start_pos = event.pos()
            cursor = Qt.ArrowCursor
            self.setCursor(cursor)
            if event.button() == Qt.RightButton:
                self.zoom_out()

    def _create_toolbar(self, parent):
        """Create a toolbar with zooming and moving options."""
        zoom_toolbar = ToolBar(parent=parent)

        self.pointer_action = QAction(icons.pointer, "Mouse", parent)
        self.pointer_action.setCheckable(True)
        self.pointer_action.setChecked(True)
        self.pointer_action.triggered.connect(self.on_mouse_point)

        self.zoom_in_action = QAction(icons.zoomIn, "Zoom In", parent)
        self.zoom_in_action.setCheckable(True)
        self.zoom_in_action.triggered.connect(self.on_mouse_zoom)

        self.move_action = QAction(icons.move, "Move", parent)
        self.move_action.setCheckable(True)
        self.move_action.triggered.connect(self.on_mouse_move)

        zoom_toolbar.addAction(self.pointer_action)
        zoom_toolbar.addAction(self.zoom_in_action)
        zoom_toolbar.addAction(self.move_action)

        size = QSize(23, 23)
        zoom_toolbar.setIconSize(size)
        zoom_toolbar.add_expander()

        return zoom_toolbar

    @Slot()
    def on_mouse_zoom(self):
        """Set the mouse mode to zoom and update cursor."""
        self.mouse_mode = MouseMode.Zoom
        cursor = Qt.CrossCursor
        self.setCursor(cursor)
        self.zoom_in_action.setChecked(True)
        self.pointer_action.setChecked(False)
        self.move_action.setChecked(False)

    @Slot()
    def on_mouse_move(self):
        """Set the mouse mode to move and update cursor."""
        self.mouse_mode = MouseMode.Move
        cursor = Qt.OpenHandCursor
        self.setCursor(cursor)
        self.move_action.setChecked(True)
        self.zoom_in_action.setChecked(False)
        self.pointer_action.setChecked(False)

    @Slot()
    def on_mouse_point(self):
        """Set the mouse mode to move and update cursor."""
        self.mouse_mode = MouseMode.Pointer
        cursor = Qt.ArrowCursor
        self.setCursor(cursor)
        self.pointer_action.setChecked(True)
        self.move_action.setChecked(False)
        self.zoom_in_action.setChecked(False)


@register_binding_controller(
    ui_name="Base 64 Image",
    klassname="Base64Image",
    binding_type=StringBinding,
    is_compatible=with_display_type("Base64Image"),
    priority=100,
    can_show_nothing=False)
class DisplayBase64Image(BaseBindingController):
    model = Instance(Base64ImageModel, args=())
    _scene = WeakRef(QGraphicsScene)

    def create_widget(self, parent):
        widget = KaraboImagePixMap(parent=parent)
        return widget

    def value_update(self, proxy):

        value = get_binding_value(proxy)

        if value is None:
            return

        _, data = extract_base64image(value)

        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.widget.zoom_out()

        if not pixmap.isNull():
            self.widget.view.pixmap_item.setPixmap(pixmap)

            pixmap_rect = pixmap.rect()
            pixmap_rect_f = QRectF(pixmap_rect)
            self.widget.view.scene.setSceneRect(pixmap_rect_f)

            self.widget.view.fitInView(pixmap_rect_f)

        else:
            self.widget.view.scene.clear()
            self.widget.view.pixmap_item.setPixmap(QPixmap())

        self.widget.view_rect = self.widget.view.scene.sceneRect()
