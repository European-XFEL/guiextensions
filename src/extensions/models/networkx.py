from xml.etree.ElementTree import SubElement

from traits.api import Bool, Float, List, String

from karabo.common.savable import BaseSavableModel
from karabo.common.scenemodel.api import BaseWidgetObjectData
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class NodePosition(BaseSavableModel):
    device_id = String()
    x = Float()
    y = Float()


class FilterInstance(BaseSavableModel):
    filter_text = String()
    is_active = Bool()


class NetworkXModel(BaseWidgetObjectData):
    nodePositions = List(NodePosition)
    filterInstances = List(FilterInstance)


def read_node_positions(element):
    positions = []

    for child_elem in element:
        if child_elem.tag != NS_KARABO + 'nodePosition':
            continue

        device_id = child_elem.get('device_id', None)

        if not device_id:
            continue

        x = float(child_elem.get('x', 0.0))
        y = float(child_elem.get('y', 0.0))

        traits = {'device_id': device_id, 'x': x, 'y': y}

        positions.append(NodePosition(**traits))

    return positions


def write_node_positions(model, element):
    for node_position in model.nodePositions:
        node_element = SubElement(element, NS_KARABO + 'nodePosition')
        for attribute in node_position.class_visible_traits():
            node_element.set(attribute,
                             str(getattr(node_position, attribute)))


def read_filter_instances(element):
    instances = []

    for child_elem in element:
        if child_elem.tag != NS_KARABO + 'filterInstance':
            continue

        filter_text = child_elem.get('filter_text', None)

        if not filter_text:
            continue

        is_active = child_elem.get('is_active', "True") == "True"

        traits = {'filter_text': filter_text, 'is_active': is_active}

        instances.append(FilterInstance(**traits))

    return instances


def write_filter_instances(model, element):
    for instance in model.filterInstances:
        filter_element = SubElement(element, NS_KARABO + 'filterInstance')
        for attribute in instance.class_visible_traits():
            filter_element.set(attribute,
                               str(getattr(instance, attribute)))


@register_scene_reader('NetworkX')
def _networkx_reader(read_func, element):
    traits = read_base_widget_data(element)
    traits['nodePositions'] = read_node_positions(element)
    traits['filterInstances'] = read_filter_instances(element)
    return NetworkXModel(**traits)


@register_scene_writer(NetworkXModel)
def _networkx_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'NetworkX')
    write_node_positions(model, element)
    write_filter_instances(model, element)
    return element
