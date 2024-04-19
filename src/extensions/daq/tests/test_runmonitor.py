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
    AccessMode, Configurable, Hash, UInt64, VectorHash, VectorUInt64)
from karabogui.conftest import gui_app
from karabogui.testing import get_class_property_proxy, set_proxy_value

from ...models.api import DisplayRunMonitorHistoryModel
from ..display_runhistory import (
    OVERVIEW_DISPLAY_TYPE, UPDATE_DISPLAY_TYPE, RunMonitorHistory)


class RunHistory(Configurable):
    proposal = UInt64(
        displayedName="Proposal",
        accessMode=AccessMode.READONLY,
    )

    runs = VectorUInt64(
        displayedName="Runs",
        accessMode=AccessMode.READONLY
    )


class Object(Configurable):
    runHistory = VectorHash(
        displayType=OVERVIEW_DISPLAY_TYPE,
        defaultValue=[],
        rows=RunHistory,
        displayedName="History",
        accessMode=AccessMode.READONLY)

    updateHistory = VectorUInt64(
        displayType=UPDATE_DISPLAY_TYPE,
        defaultValue=[],
        displayedName="History Update",
        accessMode=AccessMode.READONLY)


def _build_value():
    value = [
        Hash("proposal", 900432,
             "runs", [1, 2, 3])
    ]
    return value


@pytest.fixture
def controller_setup(gui_app: gui_app):
    schema = Object.getClassSchema()
    proxy = get_class_property_proxy(schema, "runHistory")
    controller = RunMonitorHistory(
        proxy=proxy, model=DisplayRunMonitorHistoryModel())
    controller.create(None)
    yield controller, proxy
    # teardown
    controller.destroy()
    assert controller.widget is None


def test_focus_policy(controller_setup):
    controller, _ = controller_setup
    assert controller.tree_view.focusPolicy() == Qt.StrongFocus


def test_set_value(controller_setup):
    controller, proxy = controller_setup
    item_model = controller.tree_view.model()
    assert item_model.rowCount() == 0
    set_proxy_value(proxy, "runHistory", _build_value())
    assert item_model.rowCount() == 1


def test_add_devices_proxy(controller_setup):
    schema = Object.getClassSchema()
    history_proxy = get_class_property_proxy(schema, "updateHistory")
    controller, proxy = controller_setup
    assert controller.visualize_additional_property(history_proxy)
    assert len(controller.proxies) == 2
