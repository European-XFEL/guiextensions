from xml.etree.ElementTree import SubElement

from traits.api import Int, String

from karabo.common.scenemodel.bases import BaseEditWidget, BaseWidgetObjectData
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class VectorLimitedDoubleLineEditModel(BaseEditWidget):
    """A model for VectorLimitedDoubleLineEdit Widget"""

    # The floating point precision
    decimals = Int(-1)


class LimitedDoubleLineEditModel(BaseEditWidget):
    """A model for LimitedDoubleLineEdit Widget"""
    # The floating point precision
    decimals = Int(-1)


class DetectorCellsModel(BaseWidgetObjectData):
    """A model for the LitFrameFinder widget with single pattern"""
    rows = Int(11)
    columns = Int(32)
    legend_location = String('bottom')


class MultipleDetectorCellsModel(DetectorCellsModel):
    """A model for the LitFrameFinder widget with multiple patterns"""


@register_scene_reader("VectorLimitedDoubleLineEdit")
def _vector_limited_double_line_edit_reader(element):
    traits = read_base_widget_data(element)
    decimals = element.get(NS_KARABO + "decimals", "")
    if decimals:
        traits["decimals"] = int(decimals)
    return VectorLimitedDoubleLineEditModel(**traits)


@register_scene_writer(VectorLimitedDoubleLineEditModel)
def _vector_limited_double_line_edit_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "VectorLimitedDoubleLineEdit")
    element.set(NS_KARABO + "decimals", str(model.decimals))
    return element


@register_scene_reader("LimitedDoubleLineEdit")
def _limited_double_line_edit_reader(element):
    traits = read_base_widget_data(element)
    decimals = element.get(NS_KARABO + "decimals", "")
    if decimals:
        traits["decimals"] = int(decimals)
    return LimitedDoubleLineEditModel(**traits)


@register_scene_writer(LimitedDoubleLineEditModel)
def _limited_double_line_edit_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "LimitedDoubleLineEdit")
    element.set(NS_KARABO + "decimals", str(model.decimals))
    return element


def _base_detector_cells_reader(element, model):
    traits = read_base_widget_data(element)
    traits["rows"] = int(element.get(NS_KARABO + "rows", "11"))
    traits["columns"] = int(element.get(NS_KARABO + "columns", "32"))
    traits["legend_location"] = element.get(NS_KARABO + "legend_location",
                                            "bottom")
    return model(**traits)


@register_scene_reader("DetectorCells")
def _detector_cells_reader(element):
    return _base_detector_cells_reader(element, model=DetectorCellsModel)


@register_scene_reader("MultipleDetectorCells")
def _multiple_detector_cells_reader(element):
    return _base_detector_cells_reader(element,
                                       model=MultipleDetectorCellsModel)


def _base_detector_cells_writer(model, parent, name):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, name)
    element.set(NS_KARABO + "rows", str(model.rows))
    element.set(NS_KARABO + "columns", str(model.columns))
    element.set(NS_KARABO + "legend_location", model.legend_location)


@register_scene_writer(DetectorCellsModel)
def _detector_cells_writer(model, parent):
    _base_detector_cells_writer(model, parent, name="DetectorCells")


@register_scene_writer(MultipleDetectorCellsModel)
def _multiple_detector_cells_writer(model, parent):
    _base_detector_cells_writer(model, parent, name="MultipleDetectorCells")
