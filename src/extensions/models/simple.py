from xml.etree.ElementTree import SubElement

from traits.api import Float, Int, List, Enum
from karabo.common.scenemodel.api import (
    BaseDisplayEditableWidget, BaseWidgetObjectData, read_basic_label,
    read_axes_set, read_range_set, write_basic_label, write_axes_set,
    write_range_set, BaseROIData, read_roi_info, write_roi_info, BasePlotModel)
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class IPMQuadrantModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


class DoocsTableModel(BaseWidgetObjectData):
    """ A model for the DoocsTable"""

class DoocsManagerModel(BaseWidgetObjectData):
    """ A model for the DoocsManager"""


class ScatterPositionModel(BasePlotModel):
    """ A model for the Scatter Position"""
    maxlen = Int(100)
    psize = Float(7.0)


class DynamicDigitizerModel(BasePlotModel):
    """ A model for the dynamic digitizer"""
    roi_items = List(BaseROIData)
    roi_tool = Int(0)


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


@register_scene_reader('DoocsTable')
def _doocs_table_reader(read_func, element):
    traits = read_base_widget_data(element)
    return DoocsTableModel(**traits)


@register_scene_writer(IPMQuadrantModel)
def _doocs_table_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'DoocsTable')
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
