from xml.etree.ElementTree import SubElement

from traits.trait_types import Bool

from karabo.common.scenemodel.const import WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import write_base_widget_data
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)
from karabo.common.scenemodel.widgets.graph_image import ImageGraphModel
from karabo.common.scenemodel.widgets.graph_utils import (
    read_base_karabo_image_model, write_base_karabo_image_model)


class RoiGraphModel(ImageGraphModel):
    """ A base model roi graph """
    show_scale = Bool(False)


class RectRoiGraphModel(RoiGraphModel):
    """ A model for the Rect ROI graph """


class BeamGraphModel(ImageGraphModel):
    """ A model for the beam graph """
    show_scale = Bool(False)


@register_scene_reader('RectRoiGraph')
def _roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return RectRoiGraphModel(**traits)


@register_scene_writer(RectRoiGraphModel)
def _roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'RectRoiGraph')
    write_base_karabo_image_model(model, element)
    return element


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
