#############################################################################
# Created on Jan 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import QRectF, QSize, Qt
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QAction, QGraphicsScene, QSizePolicy, QVBoxLayout, QWidget)
from traits.api import Instance, WeakRef

from karabogui.api import (
    BaseBindingController, StringBinding, get_binding_value, icons,
    register_binding_controller, with_display_type)

from .ImagePixMap import KaraboImagePixMap
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


@register_binding_controller(
    ui_name="Base 64 Image",
    klassname="Base64Image",
    binding_type=StringBinding,
    is_compatible=with_display_type("Base64Image"),
    priority=100,
    can_show_nothing=True)
class DisplayBase64Image(BaseBindingController):
    model = Instance(Base64ImageModel, args=())
    _scene = WeakRef(QGraphicsScene)
    image = WeakRef(KaraboImagePixMap)

    def create_widget(self, parent):

        widget = QWidget(parent=parent)
        layout = QVBoxLayout(widget)

        image = KaraboImagePixMap(parent=parent)

        image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image = image
        zoom_toolbar = self._create_toolbar(parent)

        layout.addWidget(zoom_toolbar)
        layout.addWidget(self.image)

        widget.setLayout(layout)

        return widget

    def value_update(self, proxy):
        value = get_binding_value(proxy)

        if value is None:
            return

        _, data = extract_base64image(value)

        pixmap = QPixmap()
        pixmap.loadFromData(data)

        if pixmap and not pixmap.isNull():
            self.image.pixmap_item.setPixmap(pixmap)

            pixmap_rect = pixmap.rect()
            pixmap_rect_f = QRectF(pixmap_rect)
            self.image.scene.setSceneRect(pixmap_rect_f)

            self.image.fitInView(pixmap_rect_f)
        else:
            self.image.scene.clear()
            self.image.pixmap_item.setPixmap(QPixmap())

        self.image.view_rect = self.image.scene.sceneRect()

    def _create_toolbar(self, parent):
        """Create a toolbar with zooming and moving options."""

        zoom_toolbar = ToolBar(parent=parent)

        zoom_in_action = QAction(icons.zoomIn, "Zoom In", parent)
        zoom_in_action.triggered.connect(self.on_mouse_zoom)

        move_action = QAction(icons.move, "Move", parent)
        move_action.triggered.connect(self.on_mouse_move)
        zoom_toolbar.addAction(zoom_in_action)
        zoom_toolbar.addAction(move_action)
        size = QSize(23, 23)
        zoom_toolbar.setIconSize(size)
        zoom_toolbar.add_expander()

        return zoom_toolbar

    def on_mouse_zoom(self):
        """Set the mouse mode to zoom and update cursor."""
        self.image.mouseMode = "Zoom"
        cursor = Qt.CrossCursor
        self.set_cursor(cursor)

    def on_mouse_move(self):
        """Set the mouse mode to move and update cursor."""
        self.image.mouseMode = "Move"
        cursor = Qt.OpenHandCursor
        self.image.setCursor(cursor)

    def set_cursor(self, cursor):
        self.image.setCursor(cursor)
