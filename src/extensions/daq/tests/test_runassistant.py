# This file is part of the Karabo Gui.
#
# http://www.karabo.eu
#
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#
# The Karabo Gui is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 3 or higher.
#
# You should have received a copy of the General Public License, version 3,
# along with the Karabo Gui.
# If not, see <https://www.gnu.org/licenses/gpl-3.0>.
#
# The Karabo Gui is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
import pytest
from qtpy.QtCore import Qt

from karabo.native import (
    AccessMode, Bool, Configurable, Hash, String, VectorHash, VectorString)
from karabogui.conftest import gui_app
from karabogui.testing import get_class_property_proxy, set_proxy_value

from ...models.api import EditableAssistantOverviewModel
from ..edit_runassistant import (
    DEVICES_DISPLAY_TYPE, OVERVIEW_DISPLAY_TYPE, RunAssistantEdit)


class AvailableGroupSchema(Configurable):
    selected = Bool(
        defaultValue=False,
        displayedName="Select",
        accessMode=AccessMode.RECONFIGURABLE)

    name = String(
        displayedName="Group Name",
        defaultValue="",
        accessMode=AccessMode.READONLY)

    groupId = String(
        displayedName="Group Id",
        defaultValue="",
        accessMode=AccessMode.READONLY)


class AvailableGroupDevices(Configurable):
    groupId = String(
        displayedName="GroupId",
        defaultValue="",
        accessMode=AccessMode.READONLY)

    sources = VectorString(
        displayedName="Sources",
        defaultValue=[],
        accessMode=AccessMode.READONLY)


class Object(Configurable):
    groupDevices = VectorHash(
        displayType=DEVICES_DISPLAY_TYPE,
        defaultValue=[],
        rows=AvailableGroupDevices,
        displayedName="Available group devices",
        accessMode=AccessMode.READONLY)

    availableGroups = VectorHash(
        displayType=OVERVIEW_DISPLAY_TYPE,
        defaultValue=[],
        rows=AvailableGroupSchema,
        displayedName="Available group configurations",
        accessMode=AccessMode.RECONFIGURABLE)


def _build_value():
    value = [
        Hash("groupId", "TESTID",
             "name", "TEST/LAB/TESTID",
             "selected", False)
    ]
    return value


@pytest.fixture
def controller_setup(gui_app: gui_app):
    schema = Object.getClassSchema()
    proxy = get_class_property_proxy(schema, "availableGroups")
    controller = RunAssistantEdit(
        proxy=proxy, model=EditableAssistantOverviewModel())
    controller.create(None)
    yield controller, proxy
    # teardown
    controller.destroy()
    assert controller.widget is None


def test_focus_policy(controller_setup):
    controller, _ = controller_setup
    assert controller.tree_widget.focusPolicy() == Qt.StrongFocus


def test_set_value(controller_setup):
    controller, proxy = controller_setup
    item_model = controller.tree_widget.model()
    assert item_model.rowCount() == 0
    set_proxy_value(proxy, "availableGroups", _build_value())
    assert item_model.rowCount() == 1


def test_edit_value(controller_setup):
    controller, proxy = controller_setup
    value = _build_value()
    set_proxy_value(proxy, "availableGroups", value)
    item_model = controller.tree_widget.model()
    root = item_model.sourceModel().invisibleRootItem()
    child = root.child(0)
    state = (Qt.Unchecked if child.checkState() == Qt.Checked
             else Qt.Checked)
    child.setCheckState(state)
    assert proxy.edit_value != value


def test_add_devices_proxy(controller_setup):
    schema = Object.getClassSchema()
    group_proxy = get_class_property_proxy(schema, "groupDevices")
    controller, proxy = controller_setup
    controller.visualize_additional_property(group_proxy)
    assert len(controller.proxies) == 2
