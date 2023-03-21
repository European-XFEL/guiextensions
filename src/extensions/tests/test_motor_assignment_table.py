from unittest import main

from qtpy.QtCore import QModelIndex, Qt

from extensions.edit_motor_stage_table import (
    CompleterDelegate, EditableAssignmentTable, MotorCompleterDelegate)
from karabo.native import (
    AccessMode, Configurable, Hash, String, VectorHash, VectorString)
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash


class TerminalAssignment(Configurable):
    terminalId = String(
        displayedName="Terminal Id",
        description="Karabo device ID associated to the PLC terminal",
        defaultValue="")

    stagePresetId = String(
        displayedName="Stage Preset ID",
        description="Inventory QR code of the stage plugged to the PLC "
                    "terminal",
        defaultValue="")


class Object(Configurable):
    terminalOptions = VectorString(
        defaultValue=["Terminal0", "Terminal1"])

    stageOptions = VectorString(
        defaultValue=["QR0", "QR1"])

    prop = VectorHash(displayType="MotorStageAssignmentTable",
                      accessMode=AccessMode.RECONFIGURABLE,
                      rows=TerminalAssignment)


def get_table_hash(num=1):
    h = Hash()
    hash_list = []
    for i in range(num):
        row = Hash("terminalId", f"Terminal{i}",
                   "stagePresetId", f"QR{i}")
        hash_list.append(row)

    h["prop"] = hash_list
    return h


class TestAssignmentTable(GuiTestCase):
    def setUp(self):
        super().setUp()
        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller = EditableAssignmentTable(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        super().tearDown()
        self.controller.destroy()
        self.controller = None

    def assertTableModel(self, row, col, result, role=Qt.DisplayRole):
        model = self.controller.sourceModel()
        self.assertEqual(model.index(row, col).data(role=role), result)

    def test_delegate(self):
        delegate = self.controller.tableWidget().itemDelegateForColumn(0)
        self.assertIsInstance(delegate, MotorCompleterDelegate)
        editor = delegate.createEditor(self.controller.tableWidget(), None,
                                       QModelIndex())
        self.assertFalse(editor.completer().caseSensitivity())

        delegate = self.controller.tableWidget().itemDelegateForColumn(1)
        editor = delegate.createEditor(self.controller.tableWidget(), None,
                                       QModelIndex())
        self.assertIsInstance(delegate, CompleterDelegate)
        self.assertEqual(delegate.proxy, self.controller.stageOptions)
        self.assertFalse(editor.completer().caseSensitivity())

    def test_set_value(self):
        self.assertEqual(self.controller.sourceModel().rowCount(None), 0)
        set_proxy_hash(self.proxy, get_table_hash())
        self.assertEqual(self.controller.sourceModel().rowCount(None), 1)
        self.assertTableModel(0, 0, "Terminal0")
        self.assertTableModel(0, 1, "QR0")

        set_proxy_hash(self.proxy, get_table_hash(num=2))
        self.assertTableModel(1, 0, "Terminal1")
        self.assertTableModel(1, 1, "QR1")
        self.assertEqual(self.controller.sourceModel().rowCount(None), 2)


if __name__ == "__main__":
    main()
