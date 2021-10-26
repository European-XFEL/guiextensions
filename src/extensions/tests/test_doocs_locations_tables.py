from unittest import main

from extensions.display_doocs_location_table import DisplayDoocsLocationTable
from karabo.native import AccessMode, Configurable, Hash, String, VectorHash
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
        self.assertEqual(self.controller._item_model.rowCount(None),
                         len(INIT_TABLE_DIKT))
        self.assertTableModel(0, 0, INIT_TABLE_DIKT[0]["server"])
        self.assertTableModel(0, 1, INIT_TABLE_DIKT[0]["properties"])
        self.assertTableModel(1, 0, INIT_TABLE_DIKT[1]["server"])
        self.assertTableModel(1, 1, INIT_TABLE_DIKT[1]["properties"])

        # Add one row to the table
        INIT_TABLE_DIKT.append(EXTRA_TABLE_ROW)
        set_proxy_hash(self.proxy, get_table_hash())
        self.assertTableModel(2, 0, INIT_TABLE_DIKT[2]["server"])
        self.assertTableModel(2, 1, INIT_TABLE_DIKT[2]["properties"])


if __name__ == "__main__":
    main()
