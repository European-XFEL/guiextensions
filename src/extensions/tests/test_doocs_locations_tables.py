from unittest import main

from qtpy.QtCore import QItemSelectionModel

from ..display_doocs_location_table import DisplayDoocsLocationTable
from karabo.native import (
    AccessMode, Configurable, Hash, String, VectorHash)
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash


INIT_TABLE_DIKT = [
    {"server": "EUXFEL.LASER/LASER.CONTROL/LASER2",
     "properties": '["LOG", "NAME"]'},
    {"server": "EUXFEL.FEL/MCP.SA1/NAMES",
     "properties": '["IDEXT"]'}]
EXTRA_TABLE_ROW = {
    "server": "EUXFEL.UTIL/CORRELATION/XFELCPUXGMXTD2._SVR",
    "properties": '["MESSAGE"]'}


class DoocsLocationsSchema(Configurable):
    server = String(
        defaultValue="",
        description="The name of the DOOCS server",
        accessMode=AccessMode.READONLY)

    properties = String(
        defaultValue="",
        description="The properties in the DOOCS server",
        accessMode=AccessMode.READONLY)


class Object(Configurable):
    prop = VectorHash(displayType="DoocsLocationTable",
                      accessMode=AccessMode.READONLY,
                      rows=DoocsLocationsSchema)


def get_table_hash():
    h = Hash()
    hash_list = []
    for table_row in INIT_TABLE_DIKT:
        server = table_row["server"]
        properties = table_row["properties"]
        row = Hash("server", server, "properties", properties)
        hash_list.append(row)

    h["prop"] = hash_list
    return h


class TestDoocsLocationTable(GuiTestCase):
    def setUp(self):
        super().setUp()
        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller = DisplayDoocsLocationTable(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        super().tearDown()
        self.controller.destroy()
        self.controller = None

    def assertTableModel(self, row, col, result):
        model = self.controller._item_model
        self.assertEqual(model.index(row, col).data(), result)

    def test_set_value(self):
        # table empty at start-up
        self.assertEqual(self.controller._item_model.rowCount(None), 0)
        # read input table
        set_proxy_hash(self.proxy, get_table_hash())
        self.assertEqual(self.controller._item_model.rowCount(None), 2)
        self.assertTableModel(0, 0, INIT_TABLE_DIKT[0]["server"])
        self.assertTableModel(0, 1, INIT_TABLE_DIKT[0]["properties"])
        self.assertTableModel(1, 0, INIT_TABLE_DIKT[1]["server"])
        self.assertTableModel(1, 1, INIT_TABLE_DIKT[1]["properties"])

        set_proxy_hash(self.proxy, get_table_hash())
        self.assertEqual(self.controller._item_model.rowCount(None), 2)

        selection = self.controller.widget.selectionModel()
        index = self.controller._item_model.index(0, 0)
        selection.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)
        self.assertEqual(self.controller.configName, "config0")
        self.assertEqual(self.controller.instanceId, "TestDevice")


if __name__ == "__main__":
    main()
