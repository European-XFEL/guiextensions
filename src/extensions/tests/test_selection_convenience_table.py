from unittest import main

from qtpy.QtCore import Qt

from extensions.edit_selection_table import (
    NO_COLUMN_TOOLTIP, SelectionMethod, SelectionTable)
from karabo.native import (
    AccessMode, Bool, Configurable, Hash, String, VectorHash)
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash


class ViewSchema(Configurable):
    selected = Bool(defaultValue=False,
                    displayType="TableSelection")

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
    prop = VectorHash(accessMode=AccessMode.RECONFIGURABLE,
                      rows=ViewSchema)


# broken because of now column with TableSelection displayType
class ViewSchemaBroken1(Configurable):
    selected = Bool(defaultValue=False)

    deviceId = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)

    classId = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)

    status = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)


class ObjectBroken1(Configurable):
    prop = VectorHash(accessMode=AccessMode.RECONFIGURABLE,
                      rows=ViewSchemaBroken1)


# broken because of two selection columns
class ViewSchemaBroken2(Configurable):
    selected = Bool(defaultValue=False,
                    displayType="TableSelection")

    selected2 = Bool(defaultValue=False,
                     displayType="TableSelection")

    deviceId = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)

    classId = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)

    status = String(
        defaultValue="",
        accessMode=AccessMode.READONLY)


class ObjectBroken2(Configurable):
    prop = VectorHash(accessMode=AccessMode.RECONFIGURABLE,
                      rows=ViewSchemaBroken2)


def get_table_hash(num=1):
    h = Hash()
    hash_list = []
    for i in range(num):
        row = Hash("selected", False,
                   "deviceId", f"XHQ_EG_DG/MOTOR/MOTOR{i}",
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
        self.controller = SelectionTable(proxy=self.proxy)
        self.controller.create(None)
        self.controller.tableWidget().model().setFilterKeyColumn(1)

    def tearDown(self):
        super().tearDown()
        self.controller.destroy()
        self.controller = None

    def assertTableModel(self, row, col, result, role=Qt.DisplayRole):
        model = self.controller.sourceModel()
        self.assertEqual(model.index(row, col).data(role=role), result)

    def test_selections(self):
        num = 42
        self.assertEqual(self.controller.sourceModel().rowCount(None), 0)
        set_proxy_hash(self.proxy, get_table_hash(num=num))
        self.assertEqual(self.controller.sourceModel().rowCount(None), num)
        for i in range(num):
            self.assertTableModel(i, 0, "False")
            self.assertTableModel(i, 1, f"XHQ_EG_DG/MOTOR/MOTOR{i}")
            self.assertTableModel(i, 2, "BeckhoffAdvancedMotor")
            self.assertTableModel(i, 3, "ON")
        # set a filter, then select all
        self.controller.searchLabel.setText("MOTOR1")
        self.controller.searchLabel.textChanged.emit("MOTOR1")
        self.controller._change_selection(SelectionMethod.ALL)
        self.assertEqual(self.controller.sourceModel().rowCount(None), num)
        for i in range(num):
            self.assertTableModel(i, 0, str(str(i).startswith("1")))
            self.assertTableModel(i, 1, f"XHQ_EG_DG/MOTOR/MOTOR{i}")
            self.assertTableModel(i, 2, "BeckhoffAdvancedMotor")
            self.assertTableModel(i, 3, "ON")

        # remove filter and invert
        self.controller.searchLabel.setText("")
        self.controller._change_selection(SelectionMethod.INVERT)
        self.assertEqual(self.controller.sourceModel().rowCount(None), num)
        for i in range(num):
            self.assertTableModel(i, 0, str(not str(i).startswith("1")))
            self.assertTableModel(i, 1, f"XHQ_EG_DG/MOTOR/MOTOR{i}")
            self.assertTableModel(i, 2, "BeckhoffAdvancedMotor")
            self.assertTableModel(i, 3, "ON")

        # add filter again and deselect all
        self.controller.searchLabel.setText("MOTOR")
        self.controller._change_selection(SelectionMethod.NONE)
        self.assertEqual(self.controller.sourceModel().rowCount(None), num)
        for i in range(num):
            self.assertTableModel(i, 0, "False")
            self.assertTableModel(i, 1, f"XHQ_EG_DG/MOTOR/MOTOR{i}")
            self.assertTableModel(i, 2, "BeckhoffAdvancedMotor")
            self.assertTableModel(i, 3, "ON")

    def test_non_compatible_cases(self):
        # non-compatible because of no TableSelection DisplayType
        schema = ObjectBroken1.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller.binding_update(self.proxy)
        # buttons should be disabled
        for button in self.controller.buttons:
            self.assertFalse(button.isEnabled())
        self.assertEqual(self.controller.tableWidget().toolTip(),
                         NO_COLUMN_TOOLTIP)

        # set a working schema again
        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller.binding_update(self.proxy)
        # buttons should be enabled
        for button in self.controller.buttons:
            self.assertTrue(button.isEnabled())
        self.assertEqual(self.controller.tableWidget().toolTip(),
                         self.controller.originalToolTip)

        # non-compatible because of two TableSelection DisplayTypes
        schema = ObjectBroken2.getClassSchema()
        self.proxy = get_property_proxy(schema, "prop")
        self.controller.binding_update(self.proxy)
        # buttons should be disabled
        for button in self.controller.buttons:
            self.assertFalse(button.isEnabled())
        self.assertEqual(self.controller.tableWidget().toolTip(),
                         NO_COLUMN_TOOLTIP)


if __name__ == "__main__":
    main()
