from xml.etree.ElementTree import SubElement

from traits.api import Bool, Enum, Float, Int, List, String
from karabo.common.scenemodel.api import (
    BaseDisplayEditableWidget, BasePlotModel, BaseROIData,
    BaseWidgetObjectData, ImageGraphModel, read_axes_set,
    read_base_karabo_image_model, read_basic_label, read_range_set,
    read_roi_info, write_axes_set, write_base_karabo_image_model,
    write_basic_label, write_range_set, write_roi_info)
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class IPMQuadrantModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


class ScatterPositionModel(BasePlotModel):
    """ A model for the Scatter Position"""
    maxlen = Int(100)
    psize = Float(7.0)


class DynamicDigitizerModel(BasePlotModel):
    """ A model for the dynamic digitizer"""
    roi_items = List(BaseROIData)
    roi_tool = Int(0)


class MetroRoiGraphModel(ImageGraphModel):
    """ A model for the metro beamstop graph """
    show_scale = Bool(False)
    image_path = String


class MetroCircleRoiGraphModel(MetroRoiGraphModel):
    """ A model for the metro beamstop graph """
    center_path = String
    radius_path = String


class MetroRectRoiGraphModel(MetroRoiGraphModel):
    """ A model for the metro ROI graph """
    roi_path = String


class ScantoolBaseModel(BaseWidgetObjectData):
    """ A model for the Scantool Base Widget """


class PointAndClickModel(BaseDisplayEditableWidget):
    """ A model for the Point-And-Click Widget"""
    klass = Enum('DisplayPointAndClick', 'EditablePointAndClick')


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


@register_scene_reader('DynamicDigitizer')
def _dynamic_digitizer_reader(read_func, element):
    traits = read_base_widget_data(element)
    traits.update(read_basic_label(element))
    traits.update(read_axes_set(element))
    traits.update(read_range_set(element))
    # roi information
    traits['roi_items'] = read_roi_info(element)
    traits['roi_tool'] = int(element.get(NS_KARABO + 'roi_tool', 0))

    return DynamicDigitizerModel(**traits)


@register_scene_writer(DynamicDigitizerModel)
def _dynamic_digitizer_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'DynamicDigitizer')
    write_basic_label(model, element)
    write_axes_set(model, element)
    write_range_set(model, element)
    # roi information
    write_roi_info(model, element)
    element.set(NS_KARABO + 'roi_tool', str(model.roi_tool))

    return element


@register_scene_reader('MetroCircleRoiGraph')
def _metro_circle_roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return MetroCircleRoiGraphModel(**traits)


@register_scene_writer(MetroCircleRoiGraphModel)
def _metro_circle_roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroCircleRoiGraph')
    write_base_karabo_image_model(model, element)
    return element


@register_scene_reader('MetroRectRoiGraph')
def _metro_rect_roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return MetroRectRoiGraphModel(**traits)


@register_scene_writer(MetroRectRoiGraphModel)
def _metro_rect_roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroRectRoiGraph')
    write_base_karabo_image_model(model, element)
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


@register_scene_reader('DisplayPointAndClick')
def _pac_ro_reader(read_func, element):
    traits = read_base_widget_data(element)
    return PointAndClickModel(klass='DisplayPointAndClick', **traits)


@register_scene_reader('EditablePointAndClick')
def _pac_edit_reader(read_func, element):
    traits = read_base_widget_data(element)
    return PointAndClickModel(klass='EditablePointAndClick', **traits)


@register_scene_writer(PointAndClickModel)
def _pac_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, model.klass)
    return element
