from xml.etree.ElementTree import SubElement

from traits.api import Bool, Int

from karabo.common.scenemodel.api import BaseWidgetObjectData
from karabo.common.scenemodel.bases import BaseEditWidget
from karabo.common.scenemodel.const import WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)

from .utils import (
    update_base_table, update_filter_table, write_base_table,
    write_filter_table)

# Enter your model here if you have a generic table (type).
# Model must have __NAME__Model. Widget must have __NAME__ as class name.
# If the table has more properties than the generic ones, an own reader
# and writer must be created.
TABLE_WIDGET_MODELS = (
    # (TableModelName, Filtering: Bool)
    ("CriticalCompareViewModel", True),
    ("DoocsLocationTableModel", False),
    ("DoocsMirrorTableModel", True),
    ("DeviceReconfigurationTableModel", True),
    ("MotorAssignmentTableModel", True),
    ("MotorParametersTableModel", True),
    ("SelectionTableModel", True),
    ("NotificationConfigurationTableModel", True),
)


class CriticalCompareViewModel(BaseWidgetObjectData):
    """ A model for the Operational Historian Table Element"""
    resizeToContents = Bool(True)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(True)


class DoocsLocationTableModel(BaseWidgetObjectData):
    """ A model for the Doocs Location"""
    resizeToContents = Bool(False)


class DoocsMirrorTableModel(BaseWidgetObjectData):
    """ A model for the Doocs Mirror"""
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(True)


class MotorAssignmentTableModel(BaseEditWidget):
    """A model for the Assignment Table device"""
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(True)


class MotorParametersTableModel(BaseEditWidget):
    """A model for the Motor Parameters Table"""
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(True)


class DeviceReconfigurationTableModel(BaseWidgetObjectData):
    """A model for the Device Reconfiguration Table"""
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(True)


class SelectionTableModel(BaseEditWidget):
    """A model for the convenience selections in a Table"""
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(False)


class NotificationConfigurationTableModel(BaseEditWidget):
    """A model for the notification configuration in a Table"""
    resizeToContents = Bool(False)
    filterKeyColumn = Int(0)
    sortingEnabled = Bool(False)


def _built_table_readers_writers():
    """ Build readers and writers for the table models

    The name of the model must have `__NAME__Model`.
    """

    def _build_table_reader(klass, has_filter=False):
        """Create a table reader for base and filter table"""

        def base_reader(element):
            traits = read_base_widget_data(element)
            traits.update(update_base_table(element))
            return klass(**traits)

        def filter_reader(element):
            traits = read_base_widget_data(element)
            traits.update(update_filter_table(element))
            return klass(**traits)

        return base_reader if not has_filter else filter_reader

    def _build_table_writer(name, has_filter=False):
        """Create a table writer for base and filter table"""

        def base_writer(model, parent):
            element = SubElement(parent, WIDGET_ELEMENT_TAG)
            write_base_widget_data(model, element, name)
            write_base_table(model, element)
            return element

        def filter_writer(model, parent):
            element = SubElement(parent, WIDGET_ELEMENT_TAG)
            write_base_widget_data(model, element, name)
            write_filter_table(model, element)
            return element

        return base_writer if not has_filter else filter_writer

    for model_name, has_filter in TABLE_WIDGET_MODELS:
        # if a model name does not end with "Model" the name will be clipped.
        assert model_name.endswith("Model")
        klass = globals()[model_name]
        file_name = model_name[:-len("Model")]
        register_scene_reader(file_name)(
            _build_table_reader(klass, has_filter=has_filter))
        register_scene_writer(klass)(
            _build_table_writer(file_name, has_filter=has_filter))


_built_table_readers_writers()
