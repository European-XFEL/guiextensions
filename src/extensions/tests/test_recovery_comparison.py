from unittest import main

from qtpy.QtCore import QItemSelectionModel, Qt

from extensions.display_critical_compare_view import DisplayCriticalCompareView
from karabo.native import AccessMode, Configurable, Hash, String, VectorHash
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash


class ViewSchema(Configurable):
    deviceId = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)

    classId = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)

    status = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)


class Object(Configurable):
    prop = VectorHash(displayType="RecoveryCompareView",
                      accessMode=AccessMode.READONLY,
                      rows=ViewSchema)


def get_table_hash(num=1):
    h = Hash()
    hash_list = []
    for i in range(num):
        row = Hash("deviceId", f"XHQ_EG_DG/MOTOR/MOTOR{i}",
                   "classId", "BeckhoffAdvancedMotor",
                   "status", "ON")
        hash_list.append(row)

    h["prop"] = hash_list
    return h


class TestComponentView(GuiTestCase):
    def setUp(self):
        super().setUp()
        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller = DisplayCriticalCompareView(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        super().tearDown()
        self.controller.destroy()
        self.controller = None

    def assertTableModel(self, row, col, result, role=Qt.DisplayRole):
        model = self.controller.sourceModel()
        self.assertEqual(model.index(row, col).data(role=role), result)

    def test_set_value(self):
        self.assertEqual(self.controller.sourceModel().rowCount(None), 0)
        set_proxy_hash(self.proxy, get_table_hash())
        self.assertEqual(self.controller.sourceModel().rowCount(None), 1)
        self.assertTableModel(0, 0, "XHQ_EG_DG/MOTOR/MOTOR0")
        self.assertTableModel(0, 1, "BeckhoffAdvancedMotor")
        self.assertTableModel(0, 2, "ON")

        set_proxy_hash(self.proxy, get_table_hash(4))
        self.assertEqual(self.controller.sourceModel().rowCount(None), 4)
        selection = self.controller.tableWidget().selectionModel()
        index = self.controller.sourceModel().index(0, 0)
        selection.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)
        self.assertEqual(self.controller.getInstanceId(), "TestDevice")


if __name__ == "__main__":
    main()
