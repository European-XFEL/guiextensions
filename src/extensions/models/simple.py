from xml.etree.ElementTree import SubElement

from traits.api import Bool, Enum, Int, String

from karabo.common.scenemodel.api import (
    BaseDisplayEditableWidget, BaseWidgetObjectData, ImageGraphModel)
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


class DisplayConditionCommand(BaseWidgetObjectData):
    """ A model for the Condition Command Base Widget """


class ROIAnnotateModel(ImageGraphModel):
    """ A model for Image Annotation"""
    coordinateDevice = String('')


class ScantoolBaseModel(BaseWidgetObjectData):
    """ A model for the Scantool Base Widget """


class ScantoolDeviceViewModel(BaseEditWidget):
    """A model for the ScantoolDeviceViewModel device"""


class MotorAssignmentTableModel(BaseEditWidget):
    """A model for the Assignment Table device"""


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


class DetectorCellsModel(BaseWidgetObjectData):
    """A model for the AgipdLitFrameFinder"""


class RecoveryReportTableModel(BaseWidgetObjectData):
    """A model for the Report Table of the RecoveryPortal"""


class SelectionTableModel(BaseEditWidget):
    """A model for the convenience selections in a Table"""

    # True if the table is resizing the columns to contents
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(False)


# Reader and writers ...
# --------------------------------------------------------------------------


# Model must have __NAME__Model. Widget must have __NAME__ as class name
_SIMPLE_WIDGET_MODELS = (
    "IPMQuadrantModel", "DoocsLocationTableModel", "DoocsMirrorTableModel",
    "PulseIdMapModel", "DynamicPulseIdMapModel", "CriticalCompareViewModel",
    "RecoveryReportTableModel", "DisplayConditionCommand",
    "DetectorCellsModel", "MotorAssignmentTableModel")

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


@register_scene_reader('Scantool-Device-View')
def _scantool_device_view_reader(element):
    traits = read_base_widget_data(element)
    return ScantoolDeviceViewModel(**traits)


@register_scene_writer(ScantoolDeviceViewModel)
def _scantool_device_view_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'Scantool-Device-View')
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


@register_scene_reader('SelectionTable')
def _selection_convenience_table_reader(read_func, element):
    traits = read_base_widget_data(element)
    # copied from filter table
    resizeToContents = element.get(NS_KARABO + 'resizeToContents', '')
    resizeToContents = resizeToContents.lower() == 'true'
    traits['resizeToContents'] = resizeToContents
    filterKeyColumn = int(element.get(NS_KARABO + 'filterKeyColumn', 0))
    traits['filterKeyColumn'] = filterKeyColumn
    return SelectionTableModel(**traits)


@register_scene_writer(SelectionTableModel)
def _selection_convenience_table_write(write_func, model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'SelectionTable')
    # copied from filter table
    element.set(NS_KARABO + 'resizeToContents',
                str(model.resizeToContents).lower())
    element.set(NS_KARABO + 'filterKeyColumn', str(model.filterKeyColumn))
    return element


@register_scene_reader('ROIAnnotate')
def _image_annotate_reader(element):
    traits = read_base_widget_data(element)
    traits['aux_plots'] = int(element.get(NS_KARABO + 'aux_plots', '0'))
    traits['colormap'] = element.get(NS_KARABO + 'colormap', "viridis")
    traits['aspect_ratio'] = int(element.get(NS_KARABO + 'aspect_ratio', 1))
    show_scale = element.get(NS_KARABO + 'show_scale', '1')
    traits['show_scale'] = bool(int(show_scale))
    element.get(NS_KARABO + 'coordinateDevice', '')
    return ROIAnnotateModel(**traits)


@register_scene_writer(ROIAnnotateModel)
def _image_annotate_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'ROIAnnotate')
    element.set(NS_KARABO + 'colormap', model.colormap)
    element.set(NS_KARABO + 'aux_plots', str(model.aux_plots))
    element.set(NS_KARABO + 'aspect_ratio', str(model.aspect_ratio))
    show_scale = str(int(model.show_scale))
    element.set(NS_KARABO + 'show_scale', show_scale)
    element.set(NS_KARABO + 'coordinateDevice', str(model.coordinateDevice))
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
