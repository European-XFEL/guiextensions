from xml.etree.ElementTree import SubElement

from traits.api import Bool, Enum, Float, Int, List, String

from karabo.common.scenemodel.api import (
    BaseDisplayEditableWidget, BasePlotModel, BaseROIData,
    BaseWidgetObjectData, ImageGraphModel, read_base_karabo_image_model,
    read_roi_info, write_base_karabo_image_model, write_roi_info)
from karabo.common.scenemodel.bases import BaseEditWidget
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, read_empty_display_editable_widget,
    write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)

from .utils import read_base_plot, write_base_plot


class IPMQuadrantModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


class EditableDateTimeModel(BaseEditWidget):
    """ A model for the DateTime """
    time_format = String("yyyy-M-dThh:mm:ss")


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
    klass = Enum('DisplayStateAwareComponentManager',
                 'EditableStateAwareComponentManager')


class PointAndClickModel(BaseDisplayEditableWidget):
    """ A model for the Point-And-Click Widget"""
    klass = Enum('DisplayPointAndClick', 'EditablePointAndClick')


class RoiGraphModel(ImageGraphModel):
    """ A model for the metro ROI graph """
    show_scale = Bool(False)


class BeamGraphModel(ImageGraphModel):
    """ A model for the metro ROI graph """
    show_scale = Bool(False)


class MetroZonePlateModel(RoiGraphModel):
    """ A model for the metro ROI graph """


class PulseIdMapModel(BaseWidgetObjectData):
    """A model for the AlignedPulse device"""


class DynamicPulseIdMapModel(BaseWidgetObjectData):
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


# Reader and writers ...
# --------------------------------------------------------------------------

# Model must have __NAME__Model. Widget must have __NAME__ as class name
_SIMPLE_WIDGET_MODELS = (
    "IPMQuadrantModel", "DoocsLocationTableModel", "DoocsMirrorTableModel",
    "PulseIdMapModel", "DynamicPulseIdMapModel")

_SIMPLE_DISPLAY_EDIT_MODELS = ("StateAwareComponentManagerModel",)


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


@register_scene_reader('Scantool-Base')
def _scantool_base_reader(read_func, element):
    traits = read_base_widget_data(element)
    return ScantoolBaseModel(**traits)


@register_scene_writer(ScantoolBaseModel)
def _scantool_base_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'Scantool-Base')
    return element


@register_scene_reader('EditableDateTime')
def _date_time_edit_reader(read_func, element):
    traits = read_base_widget_data(element)
    time_format = element.get(NS_KARABO + 'time_format', '%H:%M:%S')
    traits['time_format'] = time_format
    return EditableDateTimeModel(**traits)


@register_scene_writer(EditableDateTimeModel)
def _date_time_edit_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'EditableDateTime')
    element.set(NS_KARABO + 'time_format', str(model.time_format))
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
    traits = read_base_plot(element)
    return MetroXasGraphModel(**traits)


@register_scene_writer(MetroXasGraphModel)
def _metro_xas_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'MetroXasGraph')


@register_scene_reader('BeamGraph')
def _beam_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return BeamGraphModel(**traits)


@register_scene_writer(BeamGraphModel)
def _beam_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'BeamGraph')
    write_base_karabo_image_model(model, element)
    return element


@register_scene_reader('MetroSecAxisGraph')
def _metro_secaxis_graph_reader(element):
    traits = read_base_plot(element)
    traits['x2_offset'] = float(element.get(NS_KARABO + 'x2_offset', '0'))
    traits['x2_step'] = float(element.get(NS_KARABO + 'x2_step', '1'))
    traits['vline_visible'] = bool(element.get(NS_KARABO + 'vline_visible',
                                               'False'))
    traits['vline_value'] = float(element.get(NS_KARABO + 'vline_value', '0'))
    return MetroSecAxisGraphModel(**traits)


@register_scene_writer(MetroSecAxisGraphModel)
def _metro_secaxis_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'MetroSecAxisGraph')
    element.set(NS_KARABO + 'x2_offset', str(model.x2_offset))
    element.set(NS_KARABO + 'x2_step', str(model.x2_step))
    element.set(NS_KARABO + 'vline_visible', str(model.vline_visible))
    element.set(NS_KARABO + 'vline_value', str(model.vline_value))


@register_scene_reader('MetroTwinXGraph')
def _metro_twinx_graph_reader(element):
    traits = read_base_plot(element)
    return MetroTwinXGraphModel(**traits)


@register_scene_writer(MetroTwinXGraphModel)
def _metro_twinx_graph_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'MetroTwinXGraph')


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


# ----------------------------------------------------------------------------
# Private

def _build_empty_widget_readers_and_writers():
    """ Build readers and writers for the empty widget classes

    The name of the model must have `__NAME__Model`. The __NAME__ is stripped
    out for reading and writing the class name
    """

    def _build_reader_func(klass):
        def reader(element):
            traits = read_base_widget_data(element)
            return klass(**traits)

        return reader

    def _build_writer_func(name):
        def writer(model, parent):
            element = SubElement(parent, WIDGET_ELEMENT_TAG)
            write_base_widget_data(model, element, name)
            return element

        return writer

    for model_name in _SIMPLE_WIDGET_MODELS:
        klass = globals()[model_name]
        file_name = model_name[:-len('Model')]
        register_scene_reader(file_name)(_build_reader_func(klass))
        register_scene_writer(klass)(_build_writer_func(file_name))


def _build_empty_display_editable_readers_and_writers():
    """ Build readers and writers for the empty widget classes which come in
    Editable and Display types.
    """

    def _build_reader_func(klass):
        def reader(element):
            traits = read_empty_display_editable_widget(element)
            return klass(**traits)

        return reader

    def _writer_func(model, parent):
        element = SubElement(parent, WIDGET_ELEMENT_TAG)
        write_base_widget_data(model, element, model.klass)
        return element

    for model_name in _SIMPLE_DISPLAY_EDIT_MODELS:
        klass = globals()[model_name]
        file_name = model_name[:-len('Model')]
        reader = _build_reader_func(klass)
        register_scene_reader('Display' + file_name)(reader)
        register_scene_reader('Editable' + file_name)(reader)
        register_scene_writer(klass)(_writer_func)


# Call the builders to register all the readers and writers
_build_empty_widget_readers_and_writers()
_build_empty_display_editable_readers_and_writers()
