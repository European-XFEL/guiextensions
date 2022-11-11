from xml.etree.ElementTree import SubElement

from traits.api import Int

from karabo.common.scenemodel.api import (
    NS_KARABO, WIDGET_ELEMENT_TAG, BaseEditWidget, register_scene_reader,
    register_scene_writer)
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)


class VectorLimitedDoubleLineEditModel(BaseEditWidget):
    """A model for DoubleLineEdit Widget"""

    # The floating point precision
    decimals = Int(-1)


@register_scene_reader("VectorLimitedDoubleLineEdit")
def _limited_double_line_edit_reader(element):
    traits = read_base_widget_data(element)
    decimals = element.get(NS_KARABO + "decimals", "")
    if decimals:
        traits["decimals"] = int(decimals)
    return VectorLimitedDoubleLineEditModel(**traits)


@register_scene_writer(VectorLimitedDoubleLineEditModel)
def _limited_double_line_edit_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "VectorLimitedDoubleLineEdit")
    element.set(NS_KARABO + "decimals", str(model.decimals))
    return element
