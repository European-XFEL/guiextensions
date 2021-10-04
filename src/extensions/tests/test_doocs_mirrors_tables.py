from unittest import main

from karabo.native import AccessMode, Configurable, Hash, String, VectorHash
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash

from ..display_doocs_mirror_table import DisplayDoocsMirrorTable

INIT_TABLE_DIKT = [
    {"name": "EUXFEL_LASER/LASER_CONTROL/LASER2",
     "state": "State.ON",
     "sceneLink": "Scene Link",
     "status": "None"},
    {"name": "EUXFEL_FEL/MCP_SA1/NAMES",
     "state": "State.ON",
     "sceneLink": "Scene Link",
     "status": "None"}]
EXTRA_TABLE_ROW = {
    "name": "EUXFEL_UTIL/CORRELATION/XFELCPUXGMXTD2__SVR",
    "state": "State.ON",
    "sceneLink": "Scene Link",
    "status": "None"}


class DoocsMirrorsSchema(Configurable):
    name = String(
        defaultValue="",
        description="The name of the DOOCS mirror.",
        accessMode=AccessMode.READONLY)

    state = String(
        defaultValue="",
        description="The state of the mirror connection.",
        accessMode=AccessMode.READONLY)

    sceneLink = String(
        defaultValue="",
        description="The link to the mirror scene.",
        accessMode=AccessMode.READONLY)

    status = String(
        defaultValue="",
        description="The status of the mirror.",
        accessMode=AccessMode.READONLY)


class Object(Configurable):
    prop = VectorHash(displayType="DoocsMirrorTable",
                      accessMode=AccessMode.READONLY,
                      rows=DoocsMirrorsSchema)


def get_table_hash():
    h = Hash()
    hash_list = []
    for table_row in INIT_TABLE_DIKT:
        name = table_row["name"]
        state = table_row["state"]
        scene_link = table_row["sceneLink"]
        status = table_row["status"]
        row = Hash("name", name, "state", state,
                   "sceneLink", scene_link, "status", status)
        hash_list.append(row)

    h["prop"] = hash_list
    return h


class TestDoocsMirrorTable(GuiTestCase):
    def setUp(self):
        super().setUp()
        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller = DisplayDoocsMirrorTable(proxy=self.proxy)
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

        self.assertTableModel(0, 0, INIT_TABLE_DIKT[0]["name"])
        self.assertTableModel(0, 1, INIT_TABLE_DIKT[0]["state"])
        self.assertTableModel(0, 2, INIT_TABLE_DIKT[0]["sceneLink"])
        self.assertTableModel(0, 3, INIT_TABLE_DIKT[0]["status"])
        self.assertTableModel(1, 0, INIT_TABLE_DIKT[1]["name"])
        self.assertTableModel(1, 1, INIT_TABLE_DIKT[1]["state"])
        self.assertTableModel(1, 2, INIT_TABLE_DIKT[1]["sceneLink"])
        self.assertTableModel(1, 3, INIT_TABLE_DIKT[1]["status"])

        # Add one row to the table
        INIT_TABLE_DIKT.append(EXTRA_TABLE_ROW)
        set_proxy_hash(self.proxy, get_table_hash())
        self.assertTableModel(2, 0, INIT_TABLE_DIKT[2]["name"])
        self.assertTableModel(2, 1, INIT_TABLE_DIKT[2]["state"])
        self.assertTableModel(2, 2, INIT_TABLE_DIKT[2]["sceneLink"])
        self.assertTableModel(2, 3, INIT_TABLE_DIKT[2]["status"])
        self.assertEqual(self.controller._item_model.rowCount(None),
                         len(INIT_TABLE_DIKT))


if __name__ == "__main__":
    main()
