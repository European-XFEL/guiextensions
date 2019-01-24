#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on January 24, 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from xml.etree.ElementTree import SubElement

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QFont, QFrame, QLabel
from traits.api import Instance

from karabogui.binding.api import WidgetNodeBinding
from karabogui.const import (
    ALL_OK_COLOR, WIDGET_MIN_HEIGHT)
from karabogui.util import generateObjectName

from .api import (
    BaseBindingController, BaseWidgetObjectData, read_base_widget_data,
    register_binding_controller, register_scene_reader, register_scene_writer,
    write_base_widget_data, WIDGET_ELEMENT_TAG, with_display_type)


class BPMPositionModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


@register_scene_reader('BPMPosition', version=2)
def _color_bool_reader(read_func, element):
    traits = read_base_widget_data(element)
    return BPMPositionModel(**traits)


@register_scene_writer(BPMPositionModel)
def _color_bool_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'BPMPosition')
    return element


@register_binding_controller(
    ui_name='BPM Position Widget',
    klassname='BPMPosition',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|BPMPosition'),
    priority=0)
class BPMPositionWidget(BaseBindingController):
    # The scene data model class for this controller
    model = Instance(BPMPositionModel, args=())

    def create_widget(self, parent):
        widget = QLabel(parent)
        widget.setMinimumHeight(WIDGET_MIN_HEIGHT)
        widget.setWordWrap(True)
        widget.setAlignment(Qt.AlignCenter)

        objectName = generateObjectName(self)
        style = ("QWidget#{}".format(objectName) +
                 " {{ background-color : rgba{}; }}")
        widget.setObjectName(objectName)
        sheet = style.format(ALL_OK_COLOR)
        widget.setStyleSheet(sheet)
        widget.setFrameStyle(QFrame.Box)
        widget.setFont(QFont("Times", 8, QFont.Cursive))

        return widget
