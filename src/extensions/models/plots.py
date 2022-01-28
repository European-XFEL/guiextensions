from xml.etree.ElementTree import SubElement

from traits.trait_types import Bool, Float, Int, List, String

from extensions.models.utils import read_base_plot, write_base_plot
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)
from karabo.common.scenemodel.widgets.graph_plots import BasePlotModel
from karabo.common.scenemodel.widgets.graph_utils import (
    BaseROIData, read_roi_info, write_roi_info)


class ScatterPositionModel(BasePlotModel):
    """ A model for the Scatter Position"""
    maxlen = Int(100)
    psize = Float(7.0)


class DynamicDigitizerModel(BasePlotModel):
    """ A model for the dynamic digitizer"""
    roi_items = List(BaseROIData)
    roi_tool = Int(0)


class DynamicGraphModel(BasePlotModel):
    """ A model for the dynamic plot mode"""
    half_samples = Int(6000)
    roi_items = List(BaseROIData)
    roi_tool = Int(0)
    offset = Float(0.0)
    step = Float(1.0)
    x_grid = Bool(True)
    y_grid = Bool(True)
    number = Int(10)


class ExtendedVectorXYGraph(BasePlotModel):
    """ A model for the ExtendedVectorXYGraph"""
    x_grid = Bool(True)
    y_grid = Bool(True)
    legends = List(String)


@register_scene_reader('ScatterPosition')
def _scatter_position_reader(read_func, element):
    traits = read_base_plot(element)
    traits['maxlen'] = int(element.get(NS_KARABO + 'maxlen', 100))
    traits['psize'] = float(element.get(NS_KARABO + 'psize', 7))

    return ScatterPositionModel(**traits)


@register_scene_writer(ScatterPositionModel)
def _scatter_position_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'ScatterPosition')
    element.set(NS_KARABO + 'maxlen', str(model.maxlen))
    element.set(NS_KARABO + 'psize', str(model.psize))
    return element


@register_scene_reader('DynamicDigitizer')
def _dynamic_digitizer_reader(read_func, element):
    traits = read_base_plot(element)
    # roi information
    traits['roi_items'] = read_roi_info(element)
    traits['roi_tool'] = int(element.get(NS_KARABO + 'roi_tool', 0))

    return DynamicDigitizerModel(**traits)


@register_scene_writer(DynamicDigitizerModel)
def _dynamic_digitizer_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'DynamicDigitizer')
    # roi information
    write_roi_info(model, element)
    element.set(NS_KARABO + 'roi_tool', str(model.roi_tool))

    return element


@register_scene_reader('DynamicGraph')
def _dynamic_graph_reader(read_func, element):
    traits = read_base_plot(element)
    traits['roi_items'] = read_roi_info(element)
    traits['roi_tool'] = int(element.get(NS_KARABO + 'roi_tool', 0))
    # Number of curves
    traits['number'] = int(element.get(NS_KARABO + 'number', 10))

    return DynamicGraphModel(**traits)


@register_scene_writer(DynamicGraphModel)
def _dynamic_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'DynamicGraph')
    write_roi_info(model, element)
    element.set(NS_KARABO + 'roi_tool', str(model.roi_tool))
    # Number of curves
    element.set(NS_KARABO + 'number', str(model.number))

    return element


@register_scene_reader('ExtendedVectorXYGraph')
def _extended_vector_xy_reader(read_func, element):
    traits = read_base_plot(element)
    legends = element.get(NS_KARABO + 'legends', '')
    if len(legends):
        traits['legends'] = legends.split(',')

    return ExtendedVectorXYGraph(**traits)


@register_scene_writer(ExtendedVectorXYGraph)
def _extended_vector_xy_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'ExtendedVectorXYGraph')
    element.set(NS_KARABO + 'legends', ",".join(model.legends))
    return element