from xml.etree.ElementTree import SubElement

from traits.api import Bool, String

from karabo.common.scenemodel.bases import BaseWidgetObjectData
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
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


class ROIAnnotateModel(ImageGraphModel):
    """ A model for Image Annotation"""


class ImageCrossHairGraphModel(BaseWidgetObjectData):
    """ A model for the beam graph """
    colormap = String("none")


@register_scene_reader('RectRoiGraph')
def _roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return RectRoiGraphModel(**traits)


@register_scene_writer(RectRoiGraphModel)
def _roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "RectRoiGraph")
    write_base_karabo_image_model(model, element)
    return element


@register_scene_reader("BeamGraph")
def _beam_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return BeamGraphModel(**traits)


@register_scene_writer(BeamGraphModel)
def _beam_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "BeamGraph")
    write_base_karabo_image_model(model, element)
    return element


@register_scene_reader("ROIAnnotate")
def _image_annotate_reader(element):
    traits = read_base_widget_data(element)
    traits["aux_plots"] = int(element.get(NS_KARABO + "aux_plots", "0"))
    traits["colormap"] = element.get(NS_KARABO + "colormap", "viridis")
    traits["aspect_ratio"] = int(element.get(NS_KARABO + "aspect_ratio", 1))
    show_scale = element.get(NS_KARABO + "show_scale", "1")
    traits["show_scale"] = bool(int(show_scale))
    return ROIAnnotateModel(**traits)


@register_scene_writer(ROIAnnotateModel)
def _image_annotate_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "ROIAnnotate")
    element.set(NS_KARABO + "colormap", model.colormap)
    element.set(NS_KARABO + "aux_plots", str(model.aux_plots))
    element.set(NS_KARABO + "aspect_ratio", str(model.aspect_ratio))
    show_scale = str(int(model.show_scale))
    element.set(NS_KARABO + "show_scale", show_scale)
    return element


@register_scene_reader('ImageCrossHairGraph')
def _crosshair_graph_reader(element):
    traits = read_base_widget_data(element)
    traits["colormap"] = element.get(NS_KARABO + "colormap", "viridis")
    return ImageCrossHairGraphModel(**traits)


@register_scene_writer(ImageCrossHairGraphModel)
def _crosshair_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    element.set(NS_KARABO + "colormap", model.colormap)
    write_base_widget_data(model, element, 'ImageCrossHairGraph')
    return element
