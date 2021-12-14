from unittest import main

from extensions.display_historian_table import DisplayHistorianTable
from karabo.native import AccessMode, Configurable, Hash, String, VectorHash
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash

TABLE_DEFAULT = [
    Hash({"instanceId": "EUXFEL/MOTOR/1",
          "timestring": "2021-11-02T16:45:53.553450",
          "online": "ON",
          "state": "MOVING"
          }),
    Hash({"instanceId": "EUXFEL/MOTOR/2",
          "timestring": "2021-11-02T16:45:53.553450",
          "online": "ON",
          "state": "OFF"
          })
]

EXTRA_TABLE_ROW = Hash(
    {"instanceId": "EUXFEL/MOTOR/3",
     "timestring": "2021-11-02T16:45:53.553450",
     "online": "ON",
     "state": "ERROR"
     })


class TableSchema(Configurable):
    """The schema of a row for the main device table"""

    instanceId = String(
        accessMode=AccessMode.READONLY)

    timestring = String(
        accessMode=AccessMode.READONLY)

    online = String(
        accessMode=AccessMode.READONLY,
        displayType="State",
        options=["ON", "OFF"])

    state = String(
        accessMode=AccessMode.READONLY,
        displayType="State",
        defaultValue="UNKNOWN")


class Object(Configurable):
    prop = VectorHash(displayType="HistorianTable",
                      accessMode=AccessMode.READONLY,
                      rows=TableSchema)


class TestDoocsLocationTable(GuiTestCase):
    def setUp(self):
        super().setUp()
        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller = DisplayHistorianTable(proxy=self.proxy)
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

        set_proxy_hash(self.proxy, Hash("prop", TABLE_DEFAULT))
        self.assertEqual(self.controller._item_model.rowCount(None), 2)
        self.assertTableModel(0, 0, TABLE_DEFAULT[0]["instanceId"])
        self.assertTableModel(0, 1, TABLE_DEFAULT[0]["timestring"])
        self.assertTableModel(1, 0, TABLE_DEFAULT[1]["instanceId"])
        self.assertTableModel(1, 1, TABLE_DEFAULT[1]["timestring"])

        self.assertTableModel(1, 2, TABLE_DEFAULT[1]["online"])
        self.assertTableModel(1, 3, TABLE_DEFAULT[1]["state"])

        # Add a row Hash
        TABLE_DEFAULT.append(EXTRA_TABLE_ROW)
        set_proxy_hash(self.proxy, Hash("prop", TABLE_DEFAULT))
        self.assertEqual(self.controller._item_model.rowCount(None), 3)
        self.assertTableModel(2, 0, TABLE_DEFAULT[2]["instanceId"])
        self.assertTableModel(2, 1, TABLE_DEFAULT[2]["timestring"])


if __name__ == "__main__":
    main()
