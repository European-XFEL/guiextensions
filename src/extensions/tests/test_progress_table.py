import random

from qtpy.QtCore import Qt

from extensions.display_progress_table import ProgressTable
from karabo.native import (
    AccessMode, Configurable, Float, Hash, String, VectorHash)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class ProgressRow(Configurable):
    deviceId = String(
        accessMode=AccessMode.READONLY,
        defaultValue="")

    classId = String(
        accessMode=AccessMode.READONLY,
        defaultValue="")

    progress = Float(
        accessMode=AccessMode.READONLY,
        displayType="DisplayProgressBar",
        minExc=0, maxExc=100.,
        defaultValue=0)



class Object(Configurable):
    table = VectorHash(rows=ProgressRow,
                       accessMode=AccessMode.READONLY,
                       defaultValue=[])


def make_test_table():
    n_rows = 10
    rows = []
    for i in range(n_rows):
        row = Hash()
        row["deviceId"] = f"DEVICE_{i}"
        row["classId"] = random.choice(["FOO", "BAR", "HOO"])
        row["progress"] = random.choice(range(100))
        rows.append(row)
    return rows

class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'table')
        self.controller = ProgressTable(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):

        rows = make_test_table()
        model = self.controller.widget.model()
        set_proxy_hash(self.proxy, Hash('table', rows))

        for i, row in enumerate(rows):
            for j, (col, v, _) in enumerate(row.iterall()):
                idx = model.index(i, j)
                self.assertEqual(str(v), model.data(idx))

    def test_values_is_percent(self):
        self.controller.sourceModel().value_is_percent = True
        rows = make_test_table()
        model = self.controller.widget.model()

        set_proxy_hash(self.proxy, Hash('table', rows))

        for i, row in enumerate(rows):
            for j, (col, v, _) in enumerate(row.iterall()):
                idx = model.index(i, j)
                comp = str(v)
                if col == "progress":
                    comp = f"{v:0.1f} %"
                self.assertEqual(comp, model.data(idx))

    def test_values_color_by_value(self):
        self.controller.sourceModel().color_by_value = True
        rows = make_test_table()
        model = self.controller.widget.model()

        set_proxy_hash(self.proxy, Hash('table', rows))

        for i, row in enumerate(rows):
            for j, (col, v, _) in enumerate(row.iterall()):
                idx = model.index(i, j)

                if col == "progress":
                    brush = model.data(idx, role=Qt.BackgroundRole)
                    # should be three colors
                    self.assertEqual(3, len(brush.gradient().stops()))
                else:
                    comp = str(v)
                    self.assertEqual(comp, model.data(idx))

        self.controller.sourceModel().color_by_value = False
        rows = make_test_table()
        model = self.controller.widget.model()

        set_proxy_hash(self.proxy, Hash('table', rows))

        for i, row in enumerate(rows):
            for j, (col, v, _) in enumerate(row.iterall()):
                idx = model.index(i, j)

                if col == "progress":
                    brush = model.data(idx, role=Qt.BackgroundRole)
                    # should be two colors
                    self.assertEqual(2, len(brush.gradient().stops()))
                else:
                    comp = str(v)
                    self.assertEqual(comp, model.data(idx))