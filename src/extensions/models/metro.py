from xml.etree.ElementTree import SubElement

from traits.trait_types import Bool, String

from extensions.models.images import RoiGraphModel
from extensions.models.utils import read_base_plot, write_base_plot
from karabo.common.scenemodel.const import WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import write_base_widget_data
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)
from karabo.common.scenemodel.widgets.graph_plots import BasePlotModel
from karabo.common.scenemodel.widgets.graph_utils import (
    read_base_karabo_image_model, write_base_karabo_image_model)


class MetroSecAxisGraphModel(BasePlotModel):
    """ A model for the metro second x-axis graph """
    x_label = String('delay')
    x_units = String('mm')
    x_grid = Bool(True)
    y_grid = Bool(True)


class MetroTwinXGraphModel(BasePlotModel):
    """ A model for the metro twin x-axis graph """
    x_grid = Bool(True)
    y_grid = Bool(True)
    y_label = String('dXAS')


class MetroZonePlateModel(RoiGraphModel):
    """ A model for the metro ROI graph """


class MetroXasGraphModel(BasePlotModel):
    """ A model for the metro XAS graph """
    x_label = String('Energy')
    x_units = String('eV')
    y_label = String('XAS')


@register_scene_reader('MetroSecAxisGraph')
def _metro_secaxis_graph_reader(element):
    traits = read_base_plot(element)
    return MetroSecAxisGraphModel(**traits)


@register_scene_writer(MetroSecAxisGraphModel)
def _metro_secaxis_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'MetroSecAxisGraph')


@register_scene_reader('MetroTwinXGraph')
def _metro_twinx_graph_reader(element):
    traits = read_base_plot(element)
    return MetroTwinXGraphModel(**traits)


@register_scene_writer(MetroTwinXGraphModel)
def _metro_twinx_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'MetroTwinXGraph')


@register_scene_reader('MetroZonePlate')
def _metro_zone_plate_reader(element):
    traits = read_base_karabo_image_model(element)
    return MetroZonePlateModel(**traits)


@register_scene_writer(MetroZonePlateModel)
def _metro_zone_plate_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, 'MetroZonePlate')
    write_base_karabo_image_model(model, element)
    return element


@register_scene_reader('MetroXasGraph')
def _metro_xas_graph_reader(element):
    traits = read_base_plot(element)
    return MetroXasGraphModel(**traits)


@register_scene_writer(MetroXasGraphModel)
def _metro_xas_graph_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_plot(model, element, 'MetroXasGraph')
