from xml.etree.ElementTree import SubElement

from traits.api import Bool, Enum, String

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


class EditableDateTimeModel(BaseEditWidget):
    """ A model for the DateTime """
    time_format = String("yyyy-M-dThh:mm:ss")


class CriticalCompareViewModel(BaseWidgetObjectData):
    """ A model for the Operational Historian Table Element"""


class DoocsLocationTableModel(BaseWidgetObjectData):
    """ A model for the Doocs Location"""


class DoocsMirrorTableModel(BaseWidgetObjectData):
    """ A model for the Doocs Mirror"""


class ScantoolBaseModel(BaseWidgetObjectData):
    """ A model for the Scantool Base Widget """


class StateAwareComponentManagerModel(BaseDisplayEditableWidget):
    """ A model for the Component Manager Device Selection"""
    klass = Enum('DisplayStateAwareComponentManager',
                 'EditableStateAwareComponentManager')


class PointAndClickModel(BaseDisplayEditableWidget):
    """ A model for the Point-And-Click Widget"""
    klass = Enum('DisplayPointAndClick', 'EditablePointAndClick')


class PulseIdMapModel(BaseWidgetObjectData):
    """A model for the AlignedPulse device"""


class DynamicPulseIdMapModel(BaseWidgetObjectData):
    """A model for the AlignedPulse device"""


class SpecialColumnTableElementModel(BaseWidgetObjectData):
    """ A model for SpecialColumnTableElement
    """
    color_by_value = Bool(True)
    show_value = Bool(True)
    value_is_percent = Bool(False)


class HistorianTableModel(SpecialColumnTableElementModel):
    """ A model for the Operational Historian Table Element"""


# Reader and writers ...
# --------------------------------------------------------------------------

# Model must have __NAME__Model. Widget must have __NAME__ as class name
_SIMPLE_WIDGET_MODELS = (
    "IPMQuadrantModel", "DoocsLocationTableModel", "DoocsMirrorTableModel",
    "PulseIdMapModel", "DynamicPulseIdMapModel", "CriticalCompareViewModel")

_SIMPLE_DISPLAY_EDIT_MODELS = ("StateAwareComponentManagerModel",)


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


@register_scene_reader('SpecialColumnTable')
def _special_column_table_reader(read_func, element):
    traits = read_base_widget_data(element)
    show_value = element.get(NS_KARABO + 'show_value')
    traits["show_value"] = show_value == "True"
    value_is_percent = element.get(NS_KARABO + 'value_is_percent')
    traits["value_is_percent"] = value_is_percent == "True"
    color_by_value = element.get(NS_KARABO + 'color_by_value')
    traits["color_by_value"] = color_by_value == "True"
    return SpecialColumnTableElementModel(**traits)


@register_scene_writer(SpecialColumnTableElementModel)
def _special_column_table_writer(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'SpecialColumnTable')
    element.set(NS_KARABO + 'show_value', str(model.show_value))
    element.set(NS_KARABO + 'value_is_percent', str(model.value_is_percent))
    element.set(NS_KARABO + 'color_by_value', str(model.color_by_value))
    return element


@register_scene_reader('HistorianTableModel')
def _historian_table_reader(read_func, element):
    return _special_column_table_reader(read_func, element)


@register_scene_writer(HistorianTableModel)
def _historian_table_writer(write_func, model, parent):
    return _special_column_table_writer(write_func, model, parent)


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
