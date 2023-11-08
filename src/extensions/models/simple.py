from xml.etree.ElementTree import SubElement

from traits.api import Bool, Enum, Int, String

from karabo.common.scenemodel.api import (
    BaseDisplayEditableWidget, BaseWidgetObjectData)
from karabo.common.scenemodel.bases import BaseEditWidget
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, read_empty_display_editable_widget,
    write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class IPMQuadrantModel(BaseWidgetObjectData):
    """ A model for the Intensity Position Monitor"""


class FileUploaderModel(BaseWidgetObjectData):
    """ A model for the File Uploader"""


class EditableTextOptionsModel(BaseEditWidget):
    """A model for the editable options text field"""
    strict = Bool(True)


class EditableDateTimeModel(BaseEditWidget):
    """ A model for the DateTime """
    time_format = String("yyyy-M-dThh:mm:ss")


class DisplayConditionCommandModel(BaseWidgetObjectData):
    """ A model for the Condition Command Base Widget """


class ScantoolBaseModel(BaseWidgetObjectData):
    """ A model for the Scantool Base Widget """


class ScantoolDeviceViewModel(BaseEditWidget):
    """A model to represend scantool device environment"""


class ScantoolTemplatesModel(BaseEditWidget):
    """A model to represent scantool scan templates"""


class StateAwareComponentManagerModel(BaseDisplayEditableWidget):
    """ A model for the Component Manager Device Selection"""
    klass = Enum("DisplayStateAwareComponentManager",
                 "EditableStateAwareComponentManager")


class PointAndClickModel(BaseDisplayEditableWidget):
    """ A model for the Point-And-Click Widget"""
    klass = Enum("DisplayPointAndClick", "EditablePointAndClick")


class PulseIdMapModel(BaseWidgetObjectData):
    """A model for the AlignedPulse device"""


class DynamicPulseIdMapModel(BaseWidgetObjectData):
    """A model for the AlignedPulse device"""


class DetectorCellsModel(BaseWidgetObjectData):
    """A model for the LitFrameFinder widget with single pattern"""
    rows = Int(11)
    columns = Int(32)
    legend_location = String('bottom')


class MultipleDetectorCellsModel(DetectorCellsModel):
    """A model for the LitFrameFinder widget with multiple patterns"""


class VectorLimitedIntLineEditModel(BaseEditWidget):
    """A model for Int Line edit with min and max defined by a vector"""


class LimitedIntLineEditModel(BaseEditWidget):
    """A model for Int Line edit with min and max defined two integers"""


# Reader and writers ...
# --------------------------------------------------------------------------


# Model must have __NAME__Model. Widget must have __NAME__ as class name
_SIMPLE_WIDGET_MODELS = (
    "IPMQuadrantModel", "PulseIdMapModel", "DynamicPulseIdMapModel",
    "DisplayConditionCommandModel", "VectorLimitedIntLineEditModel",
    "LimitedIntLineEditModel",
    "FileUploaderModel")

_SIMPLE_DISPLAY_EDIT_MODELS = (
    "StateAwareComponentManagerModel", "PointAndClickModel")


@register_scene_reader("Scantool-Base")  # future deprecated
@register_scene_reader("ScantoolBase")
def _scantool_base_reader(element):
    traits = read_base_widget_data(element)
    return ScantoolBaseModel(**traits)


@register_scene_writer(ScantoolBaseModel)
def _scantool_base_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "Scantool-Base")
    return element


@register_scene_reader("Scantool-Device-View")  # future deprecated
@register_scene_reader("ScantoolDeviceView")
def _scantool_device_view_reader(element):
    traits = read_base_widget_data(element)
    return ScantoolDeviceViewModel(**traits)


@register_scene_writer(ScantoolDeviceViewModel)
def _scantool_device_view_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "Scantool-Device-View")
    return element


@register_scene_reader("ScantoolTemplates")
def _scantool_templates_reader(element):
    traits = read_base_widget_data(element)
    return ScantoolTemplatesModel(**traits)


@register_scene_writer(ScantoolTemplatesModel)
def _scantool_templates_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "ScantoolTemplates")
    return element


@register_scene_reader("EditableDateTime")
def _date_time_edit_reader(element):
    traits = read_base_widget_data(element)
    time_format = element.get(NS_KARABO + "time_format", "%H:%M:%S")
    traits["time_format"] = time_format
    return EditableDateTimeModel(**traits)


@register_scene_writer(EditableDateTimeModel)
def _date_time_edit_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "EditableDateTime")
    element.set(NS_KARABO + "time_format", str(model.time_format))


@register_scene_reader("EditableTextOptions")
def _editable_options_reader(element):
    traits = read_base_widget_data(element)
    strict = element.get(NS_KARABO + "strict", "")
    strict = strict.lower() == "true"
    traits["strict"] = strict
    return EditableTextOptionsModel(**traits)


@register_scene_writer(EditableTextOptionsModel)
def _editable_options_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "EditableTextOptions")
    element.set(NS_KARABO + "strict", str(model.strict).lower())


@register_scene_reader("DetectorCells")
def _detector_cells_reader(element, model=DetectorCellsModel):
    traits = read_base_widget_data(element)
    traits["rows"] = int(element.get(NS_KARABO + "rows", "0"))
    traits["columns"] = int(element.get(NS_KARABO + "columns", "0"))
    traits["legend_location"] = element.get(NS_KARABO + "legend_location",
                                            "bottom")
    return model(**traits)


@register_scene_writer(DetectorCellsModel)
def _detector_cells_writer(model, parent, name="DetectorCells"):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, name)
    element.set(NS_KARABO + "rows", str(model.rows))
    element.set(NS_KARABO + "columns", str(model.columns))
    element.set(NS_KARABO + "legend_location", model.legend_location)


@register_scene_reader("MultipleDetectorCells")
def _multiple_detector_cells_reader(element):
    return _detector_cells_reader(element, model=MultipleDetectorCellsModel)


@register_scene_writer(MultipleDetectorCellsModel)
def _multiple_detector_cells_writer(model, parent):
    _detector_cells_writer(model, parent, name="MultipleDetectorCells")


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
        # if a model name does not end with "Model" the name will be clipped.
        assert model_name.endswith("Model")
        klass = globals()[model_name]
        file_name = model_name[:-len("Model")]
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
        # if a model name does not end with "Model" the name will be clipped.
        assert model_name.endswith("Model")
        klass = globals()[model_name]
        file_name = model_name[:-len("Model")]
        reader = _build_reader_func(klass)
        register_scene_reader("Display" + file_name)(reader)
        register_scene_reader("Editable" + file_name)(reader)
        register_scene_writer(klass)(_writer_func)


# Call the builders to register all the readers and writers
_build_empty_widget_readers_and_writers()
_build_empty_display_editable_readers_and_writers()
