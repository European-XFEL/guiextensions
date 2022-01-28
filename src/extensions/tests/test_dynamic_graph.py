from unittest import main, mock

from extensions.display_dynamic_graph import DisplayDynamicGraph
from extensions.models.plots import DynamicGraphModel
from karabo.native import AccessMode, Configurable, VectorDouble
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)


class Object(Configurable):
    prop = VectorDouble(
        defaultValue=[1.0, 2.0],
        accessMode=AccessMode.READONLY)


class TestDynamicGraph(GuiTestCase):

    def setUp(self):
        super().setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, "prop")
        self.controller = DisplayDynamicGraph(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        super().tearDown()
        self.controller.destroy()
        self.assertIsNone(self.controller.widget)

    def test_set_value(self):
        self.assertEqual(len(self.controller.curves), 10)
        curve = self.controller.curves[0]
        self.assertIsNotNone(curve)
        value = [2, 4, 6]
        set_proxy_value(self.proxy, "prop", value)
        self.assertEqual(list(curve.yData), value)

    def test_actions(self):
        controller = DisplayDynamicGraph(proxy=self.proxy,
                                         model=DynamicGraphModel())
        controller.create(None)
        self.assertEqual(len(controller.widget.actions()), 12)
        action = controller.widget.actions()[11]
        self.assertEqual(action.text(), "Number of Curves")

        self.assertEqual(controller.model.number, 10)
        self.assertEqual(len(controller.curves), 10)
        dsym = ('extensions.display_dynamic_graph.QInputDialog')
        with mock.patch(dsym) as QInputDialog:
            QInputDialog.getInt.return_value = 12, True
            action.trigger()
            self.assertEqual(controller.model.number, 12)
            self.assertEqual(len(controller.curves), 12)

        controller.destroy()


if __name__ == "__main__":
    main()
