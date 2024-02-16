#############################################################################
# Created on Jan 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import QLabel
from traits.api import Instance

try:
    from karabo.common.scenemodel.api import extract_base64image
except ImportError:
    from karabo.common.scenemodel.api import (
        convert_from_svg_image as extract_base64image)

from karabogui.api import (
    BaseBindingController, StringBinding, get_binding_value,
    register_binding_controller, with_display_type)

from .models.api import Base64ImageModel


@register_binding_controller(
    ui_name="Base 64 Image",
    klassname="Base64Image",
    binding_type=StringBinding,
    is_compatible=with_display_type("Base64Image"),
    priority=100,
    can_show_nothing=True)
class DisplayBase64Image(BaseBindingController):
    model = Instance(Base64ImageModel, args=())

    def create_widget(self, parent):
        widget = QLabel(parent=parent)
        widget.setScaledContents(True)
        widget.setStyleSheet("border: 1px solid black;")
        pixmap = QPixmap()
        widget.setPixmap(pixmap)
        return widget

    def value_update(self, proxy):
        value = get_binding_value(proxy)

        if value is None:
            self.widget.setText("No image to display")
            self.widget.setAlignment(Qt.AlignCenter)
            return

        _, data = extract_base64image(value)

        pixmap = QPixmap()
        pixmap.loadFromData(data)

        if pixmap.isNull():
            self.widget.setText("No image to display")
            self.widget.setAlignment(Qt.AlignCenter)
            return

        self.widget.setPixmap(pixmap)
