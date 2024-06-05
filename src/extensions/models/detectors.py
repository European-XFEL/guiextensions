#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on May 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from xml.etree.ElementTree import SubElement

from traits.api import Enum

from karabo.common.scenemodel.api import BaseWidgetObjectData
from karabo.common.scenemodel.const import NS_KARABO, WIDGET_ELEMENT_TAG
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)
from karabo.common.scenemodel.registry import (
    register_scene_reader, register_scene_writer)


class RunAssistantModuleSelectionModel(BaseWidgetObjectData):
    """ A model of the detector module selection for the RunAssistant """
    detector = Enum('SPB: AGIPD1M', "MID: AGIPD1M")


@register_scene_reader('RunAssistantModuleSelection')
def _run_assistant_module_selection_reader(element):
    traits = read_base_widget_data(element)
    traits["detector"] = element.get(NS_KARABO + "detector", "SPB: AGIPD1M")
    return RunAssistantModuleSelectionModel(**traits)


@register_scene_writer(RunAssistantModuleSelectionModel)
def _run_assistant_module_selection_writer(model, parent):
    element = SubElement(parent, WIDGET_ELEMENT_TAG)
    write_base_widget_data(model, element, "RunAssistantModuleSelection")
    element.set(NS_KARABO + "detector", model.detector)
    return element
