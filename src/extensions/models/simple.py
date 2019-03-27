from xml.etree.ElementTree import SubElement

from karabo.common.scenemodel.api import BaseWidgetObjectData
from karabo.common.scenemodel.const import WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class IPMQuadrantModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


@register_scene_reader('IPM-Quadrant', version=2)
def _bpm_position_reader(read_func, element):
    traits = read_base_widget_data(element)
    return IPMQuadrantModel(**traits)


@register_scene_writer(IPMQuadrantModel)
def _bpm_position_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'IPM-Quadrant')
    return element
