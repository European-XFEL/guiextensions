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


class DoocsLocationTableModel(BaseWidgetObjectData):
    """ A model for the Doocs Location"""


class DoocsMirrorTableModel(BaseWidgetObjectData):
    """ A model for the Doocs Mirror"""


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


class StateAwareComponentManagerModel(BaseDisplayEditableWidget):
    """ A model for the Component Manager Device Selection"""
    klass = Enum('StateAwareComponentManager',
                 'StateAwareComponentManager')


class PointAndClickModel(BaseDisplayEditableWidget):
    """ A model for the Point-And-Click Widget"""
    klass = Enum('DisplayPointAndClick', 'EditablePointAndClick')


class RoiGraphModel(ImageGraphModel):
    """ A model for the metro ROI graph """
    show_scale = Bool(False)


class MetroZonePlateModel(RoiGraphModel):
    """ A model for the metro ROI graph """


class PulseIdMapModel(BaseWidgetObjectData):
    """A model for the AlignedPulse device"""


class MetroXasGraphModel(BasePlotModel):
    """ A model for the metro XAS graph """
    x_label = String('Energy')
    x_units = String('eV')
    y_label = String('XAS')


class MetroTwinXGraphModel(BasePlotModel):
    """ A model for the metro twin x-axis graph """
    x_grid = Bool(True)
    y_grid = Bool(True)
    y_label = String('dXAS')


class MetroSecAxisGraphModel(BasePlotModel):
    """ A model for the metro second x-axis graph """
    x_label = String('delay')
    x_units = String('mm')
    x_grid = Bool(True)
    y_grid = Bool(True)
    # second axis properties
    x2_offset = Float(50.45)
    x2_step = Float(6.667)
    # vertical line marker
    vline_visible = Bool(False)
    vline_value = Float(-7.5675)


@register_scene_reader('IPM-Quadrant')
def _bpm_position_reader(read_func, element):
    traits = read_base_widget_data(element)
    return IPMQuadrantModel(**traits)


@register_scene_writer(IPMQuadrantModel)
def _bpm_position_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'IPM-Quadrant')
    return element


@register_scene_reader('DoocsLocationTable')
def _doocs_table_reader(read_func, element):
    traits = read_base_widget_data(element)
    return DoocsLocationTableModel(**traits)


@register_scene_writer(DoocsLocationTableModel)
def _doocs_table_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'DoocsLocationTable')
    return element


@register_scene_reader('DoocsMirrorTable')
def _doocs_mirror_table_reader(read_func, element):
    traits = read_base_widget_data(element)
    return DoocsMirrorTableModel(**traits)


@register_scene_writer(DoocsMirrorTableModel)
def _doocs_mirror_table_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'DoocsMirrorTable')
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


@register_scene_reader('StateAwareComponentManager')
def _stateaware_manager_reader(read_func, element):
    traits = read_base_widget_data(element)
    return StateAwareComponentManagerModel(**traits)


@register_scene_writer(StateAwareComponentManagerModel)
def _stateaware_manager_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'StateAwareComponentManager')
    return element


@register_scene_reader('PulseId-Map')
def _pulseid_map_reader(read_func, element):
    traits = read_base_widget_data(element)
    return PulseIdMapModel(**traits)


@register_scene_writer(PulseIdMapModel)
def _pulseid_map_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'PulseId-Map')
    return element


@register_scene_reader('MetroZonePlate')
def _roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return MetroZonePlateModel(**traits)


@register_scene_writer(MetroZonePlateModel)
def _roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroZonePlate')
    write_base_karabo_image_model(model, element)
    return element


@register_scene_reader('MetroXasGraph')
def _metro_xas_graph_reader(element):
    traits = read_base_widget_data(element)
    traits.update(read_basic_label(element))
    traits.update(read_axes_set(element))
    traits.update(read_range_set(element))
    return MetroXasGraphModel(**traits)


@register_scene_writer(MetroXasGraphModel)
def _metro_xas_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroXasGraph')
    write_basic_label(model, element)
    write_axes_set(model, element)
    write_range_set(model, element)


@register_scene_reader('MetroSecAxisGraph')
def _metro_secaxis_graph_reader(element):
    traits = read_base_widget_data(element)
    traits.update(read_basic_label(element))
    traits.update(read_axes_set(element))
    traits.update(read_range_set(element))
    traits['x2_offset'] = float(element.get(NS_KARABO + 'x2_offset', '0'))
    traits['x2_step'] = float(element.get(NS_KARABO + 'x2_step', '1'))
    traits['vline_visible'] = bool(element.get(NS_KARABO + 'vline_visible',
                                               'False'))
    traits['vline_value'] = float(element.get(NS_KARABO + 'vline_value', '0'))
    return MetroSecAxisGraphModel(**traits)


@register_scene_writer(MetroSecAxisGraphModel)
def _metro_secaxis_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroSecAxisGraph')
    write_basic_label(model, element)
    write_axes_set(model, element)
    write_range_set(model, element)
    element.set(NS_KARABO + 'x2_offset', str(model.x2_offset))
    element.set(NS_KARABO + 'x2_step', str(model.x2_step))
    element.set(NS_KARABO + 'vline_visible', str(model.vline_visible))
    element.set(NS_KARABO + 'vline_value', str(model.vline_value))


@register_scene_reader('MetroTwinXGraph')
def _metro_twinx_graph_reader(element):
    traits = read_base_widget_data(element)
    traits.update(read_basic_label(element))
    traits.update(read_axes_set(element))
    traits.update(read_range_set(element))
    return MetroTwinXGraphModel(**traits)


@register_scene_writer(MetroTwinXGraphModel)
def _metro_twinx_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroTwinXGraph')
    write_basic_label(model, element)
    write_axes_set(model, element)
    write_range_set(model, element)
