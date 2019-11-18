from xml.etree.ElementTree import SubElement

from traits.api import Bool, Float, Int, String
from karabo.common.scenemodel.api import (
    BaseWidgetObjectData, read_basic_label, read_axes_set, read_range_set,
    write_basic_label, write_axes_set, write_range_set)
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class IPMQuadrantModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


class ScatterPositionModel(BaseWidgetObjectData):
    """ A model for the Scatter Position"""
    x_label = String
    y_label = String
    x_units = String
    y_units = String
    autorange = Bool(True)
    x_grid = Bool(False)
    y_grid = Bool(False)
    x_log = Bool(False)
    y_log = Bool(False)
    x_invert = Bool(False)
    y_invert = Bool(False)
    x_min = Float(0.0)
    x_max = Float(0.0)
    y_min = Float(0.0)
    y_max = Float(0.0)

    maxlen = Int(100)
    psize = Float(7.0)


class ScantoolBaseModel(BaseWidgetObjectData):
    """ A model for the Scantool Base Widget """


@register_scene_reader('IPM-Quadrant')
def _bpm_position_reader(read_func, element):
    traits = read_base_widget_data(element)
    return IPMQuadrantModel(**traits)


@register_scene_writer(IPMQuadrantModel)
def _bpm_position_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'IPM-Quadrant')
    return element


@register_scene_reader('ScatterPosition')
def _scatter_position_reader(read_func, element):
    traits = read_base_widget_data(element)
    traits.update(read_basic_label(element))
    traits.update(read_axes_set(element))
    traits.update(read_range_set(element))
    traits['maxlen'] = int(element.get(NS_KARABO + 'maxlen', 100))
    traits['psize'] = float(element.get(NS_KARABO + 'psize', 7))

    return ScatterPositionModel(**traits)


@register_scene_writer(ScatterPositionModel)
def _scatter_position_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'ScatterPosition')
    write_basic_label(model, element)
    write_axes_set(model, element)
    write_range_set(model, element)
    element.set(NS_KARABO + 'maxlen', str(model.maxlen))
    element.set(NS_KARABO + 'psize', str(model.psize))
    return element


@register_scene_reader('Scantool-Base')
def _scantool_base_reader(read_func, element):
    traits = read_base_widget_data(element)
    return ScantoolBaseModel(**traits)


@register_scene_writer(ScantoolBaseModel)
def _scantool_base_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'Scantool-Base')
    return element
