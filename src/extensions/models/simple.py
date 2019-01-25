from xml.etree.ElementTree import SubElement

from .api import (
    BaseWidgetObjectData, read_base_widget_data, register_scene_reader,
    register_scene_writer, write_base_widget_data, WIDGET_ELEMENT_TAG)


class IPMQuadrant(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


@register_scene_reader('IPM-Quadrant', version=2)
def _bpm_position_reader(read_func, element):
    traits = read_base_widget_data(element)
    return IPMQuadrant(**traits)


@register_scene_writer(IPMQuadrant)
def _bpm_position_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'IPM-Quadrant')
    return element
