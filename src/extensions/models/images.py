from xml.etree.ElementTree import SubElement

from traits.api import Bool, Int, List, String

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
    labels = List(String)


class RectRoiGraphModel(RoiGraphModel):
    """ A model for the Rect ROI graph """


class CircleRoiGraphModel(RoiGraphModel):
    """ A model for the Circle ROI graph """


class ZonePlateGraphModel(RoiGraphModel):
    """ A model for the zone plate graph """


class BeamGraphModel(ImageGraphModel):
    """ A model for the beam graph """
    show_scale = Bool(False)


class TickedImageGraphModel(ImageGraphModel):
    """ A model for the ticked image graph """
    show_scale = Bool(False)
    aspect_ratio = Int(0)


class ROIAnnotateModel(ImageGraphModel):
    """ A model for Image Annotation"""


class ImageCrossHairGraphModel(BaseWidgetObjectData):
    """ A model for the beam graph """
    colormap = String("none")


@register_scene_reader('Rect Roi Graph')
@register_scene_reader('RectRoiGraph')
def _rect_roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    labels = element.get(NS_KARABO + "labels", "")
    if labels:
        traits["labels"] = labels.split(",")
    return RectRoiGraphModel(**traits)


@register_scene_writer(RectRoiGraphModel)
def _rect_roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "RectRoiGraph")
    write_base_karabo_image_model(model, element)
    element.set(NS_KARABO + "labels", ",".join(model.labels))
    return element


@register_scene_reader('CircleRoiGraph')
def _circle_roi_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    labels = element.get(NS_KARABO + "labels", "")
    if labels:
        traits["labels"] = labels.split(",")
    return CircleRoiGraphModel(**traits)


@register_scene_writer(CircleRoiGraphModel)
def _circle_roi_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "CircleRoiGraph")
    write_base_karabo_image_model(model, element)
    element.set(NS_KARABO + "labels", ",".join(model.labels))
    return element


@register_scene_reader('ZonePlateGraph')
def _zone_plate_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    labels = element.get(NS_KARABO + "labels", "")
    if labels:
        traits["labels"] = labels.split(",")
    return ZonePlateGraphModel(**traits)


@register_scene_writer(ZonePlateGraphModel)
def _zone_plate_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "ZonePlateGraph")
    write_base_karabo_image_model(model, element)
    element.set(NS_KARABO + "labels", ",".join(model.labels))
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


@register_scene_reader("TickedImageGraph")
def _ticked_image_graph_reader(element):
    traits = read_base_karabo_image_model(element)
    return TickedImageGraphModel(**traits)


@register_scene_writer(TickedImageGraphModel)
def _ticked_image_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "TickedImageGraph")
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
