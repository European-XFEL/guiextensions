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


class VectorGraphWithLinearRegionsModel(BasePlotModel):
    """ A model for the VectorGraphWithLinearRegions"""
    half_samples = Int(6000)
    roi_items = List(Instance(BaseROIData))
    roi_tool = Int(0)
    offset = Float(0.0)
    step = Float(1.0)
    x_grid = Bool(True)
    y_grid = Bool(True)
    number = Int(10)

    # Make the distinction between the curves and the linear regions
    linear_regions = List(String)


class VectorXYGraphWithLinearRegionsModel(VectorGraphWithLinearRegionsModel):
    """ A model for the VectorXYGraphWithLinearRegions"""
    legends = List(String)


class XYTwoAxisGraphModel(BasePlotModel):
    """ A model for the TwoAxisGraph"""
    roi_items = List(Instance(BaseROIData))
    roi_tool = Int(0)


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


class TriggerSliceGraphModel(BasePlotModel):
    """ A model for the trigger slice graph with digitizer trace plot """


class PolarPlotModel(BasePlotModel):
    """ A model for the polar plot """
    num_ellipses = Int(5)
    max_ellipses_radius = Int(100)


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


@register_scene_reader("VectorGraphWithLinearRegionsModel")
def _vector_graph_with_linear_regions_reader(element):
    traits = read_base_plot(element)
    linear_regions = element.get(NS_KARABO + "linear_regions", "")
    if len(linear_regions):
        traits["linear_regions"] = linear_regions.split(",")
    return VectorGraphWithLinearRegionsModel(**traits)


@register_scene_writer(VectorGraphWithLinearRegionsModel)
def _vector_graph_with_linear_regions_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    element.set(NS_KARABO + "linear_regions", ",".join(model.linear_regions))
    write_base_plot(model, element, "VectorGraphWithLinearRegionsModel")
    return element


@register_scene_reader("VectorXYGraphWithLinearRegionsModel")
def _vector_xy_graph_with_linear_regions_reader(element):
    traits = read_base_plot(element)
    legends = element.get(NS_KARABO + "legends", "")
    if len(legends):
        traits["legends"] = legends.split(",")
    linear_regions = element.get(NS_KARABO + "linear_regions", "")
    if len(linear_regions):
        traits["linear_regions"] = linear_regions.split(",")

    return VectorXYGraphWithLinearRegionsModel(**traits)


@register_scene_writer(VectorXYGraphWithLinearRegionsModel)
def _vector_xy_graph_with_linear_regions_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    element.set(NS_KARABO + "legends", ",".join(model.legends))
    element.set(NS_KARABO + "linear_regions", ",".join(model.linear_regions))
    write_base_plot(model, element, "VectorXYGraphWithLinearRegionsModel")
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


@register_scene_reader("XYTwoAxisGraphModel")
def _two_axis_graph_reader(element):
    traits = read_base_plot(element)
    return XYTwoAxisGraphModel(**traits)


@register_scene_writer(XYTwoAxisGraphModel)
def _two_axis_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "XYTwoAxisGraphModel")
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


@register_scene_reader("TriggerSliceGraph")
def _trigger_slice_graph_reader(element):
    traits = read_base_plot(element)
    return TriggerSliceGraphModel(**traits)


@register_scene_writer(TriggerSliceGraphModel)
def _trigger_slice_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "TriggerSliceGraph")


@register_scene_reader("PolarPlot")
def _polar_plot_reader(element):
    traits = read_base_plot(element)
    traits["num_ellipses"] = int(element.get(NS_KARABO + "num_ellipses", 5))
    traits["max_ellipses_radius"] = int(element.get(
        NS_KARABO + "max_ellipses_radius", 100))

    return PolarPlotModel(**traits)


@register_scene_writer(PolarPlotModel)
def _polar_plot_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, "PolarPlot")
    element.set(NS_KARABO + "num_ellipses", str(model.num_ellipses))
    element.set(NS_KARABO + "max_ellipses_radius",
                str(model.max_ellipses_radius))
    return element
