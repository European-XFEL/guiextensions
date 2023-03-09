from xml.etree.ElementTree import SubElement

from traits.api import Bool, Enum, Float, Instance, Int, List, String

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
    roi_items = List(Instance(BaseROIData))
    roi_tool = Int(0)


class DynamicGraphModel(BasePlotModel):
    """ A model for the dynamic plot mode"""
    half_samples = Int(6000)
    roi_items = List(Instance(BaseROIData))
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


class TableVectorXYGraphModel(BasePlotModel):
    """ A model for the TableVectorXYGraph"""
    x_grid = Bool(True)
    y_grid = Bool(True)
    legends = List(String)
    klass = Enum("DisplayTableVectorXYGraph", "EditableTableVectorXYGraph")


class XasGraphModel(BasePlotModel):
    """ A model for the metro XAS graph """
    x_label = String("Bins")
    y_label = String("XAS")


class PeakIntegrationGraphModel(BasePlotModel):
    """ A model for the peak integration graph """


class UncertaintyGraphModel(BasePlotModel):
    """ A model for the uncertainty graph """


@register_scene_reader("ScatterPosition")
def _scatter_position_reader(element):
    traits = read_base_plot(element)
    traits["maxlen"] = int(element.get(NS_KARABO + "maxlen", 100))
    traits["psize"] = float(element.get(NS_KARABO + "psize", 7))

    return ScatterPositionModel(**traits)


@register_scene_writer(ScatterPositionModel)
def _scatter_position_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "ScatterPosition")
    element.set(NS_KARABO + "maxlen", str(model.maxlen))
    element.set(NS_KARABO + "psize", str(model.psize))
    return element


@register_scene_reader("DynamicDigitizer")
def _dynamic_digitizer_reader(element):
    traits = read_base_plot(element)
    # roi information
    traits["roi_items"] = read_roi_info(element)
    traits["roi_tool"] = int(element.get(NS_KARABO + "roi_tool", 0))

    return DynamicDigitizerModel(**traits)


@register_scene_writer(DynamicDigitizerModel)
def _dynamic_digitizer_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "DynamicDigitizer")
    # roi information
    write_roi_info(model, element)
    element.set(NS_KARABO + "roi_tool", str(model.roi_tool))

    return element


@register_scene_reader("DynamicGraph")
def _dynamic_graph_reader(element):
    traits = read_base_plot(element)
    traits["roi_items"] = read_roi_info(element)
    traits["roi_tool"] = int(element.get(NS_KARABO + "roi_tool", 0))
    # Number of curves
    traits["number"] = int(element.get(NS_KARABO + "number", 10))

    return DynamicGraphModel(**traits)


@register_scene_writer(DynamicGraphModel)
def _dynamic_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "DynamicGraph")
    write_roi_info(model, element)
    element.set(NS_KARABO + "roi_tool", str(model.roi_tool))
    # Number of curves
    element.set(NS_KARABO + "number", str(model.number))

    return element


@register_scene_reader("ExtendedVectorXYGraph")
def _extended_vector_xy_reader(element):
    traits = read_base_plot(element)
    legends = element.get(NS_KARABO + "legends", "")
    if len(legends):
        traits["legends"] = legends.split(",")

    return ExtendedVectorXYGraph(**traits)


@register_scene_writer(ExtendedVectorXYGraph)
def _extended_vector_xy_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "ExtendedVectorXYGraph")
    element.set(NS_KARABO + "legends", ",".join(model.legends))
    return element


@register_scene_reader("TableVectorXYGraph")
def _table_vector_xy_reader(element):
    traits = read_base_plot(element)
    legends = element.get(NS_KARABO + "legends", "")
    if len(legends):
        traits["legends"] = legends.split(",")

    return TableVectorXYGraphModel(**traits)


@register_scene_writer(TableVectorXYGraphModel)
def _table_vector_xy_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "TableVectorXYGraph")
    element.set(NS_KARABO + "legends", ",".join(model.legends))
    return element


@register_scene_reader("XasGraph")
def _xas_graph_reader(element):
    traits = read_base_plot(element)
    return XasGraphModel(**traits)


@register_scene_writer(XasGraphModel)
def _xas_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "XasGraph")


@register_scene_reader("PeakIntegrationGraph")
def _peak_integration_graph_reader(element):
    traits = read_base_plot(element)
    return PeakIntegrationGraphModel(**traits)


@register_scene_writer(PeakIntegrationGraphModel)
def _peak_integration_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "PeakIntegrationGraph")


@register_scene_reader("UncertaintyGraph")
def _uncertainty_graph_reader(element):
    traits = read_base_plot(element)
    return UncertaintyGraphModel(**traits)


@register_scene_writer(UncertaintyGraphModel)
def _uncertainty_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "UncertaintyGraph")
