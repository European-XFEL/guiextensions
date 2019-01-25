from karabo.middlelayer import Configurable, Float, Node
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)

from ..display_ipm_quadrant import DisplayIPMQuadrant


class DataNode(Configurable):
    displayType = "WidgetNode|IPM-Quadrant"
    avgNormX = Float(defaultValue=0.1)
    avgNormY = Float(defaultValue=-0.7)


class Object(Configurable):
    node = Node(DataNode)


class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = DisplayIPMQuadrant(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):
        set_proxy_value(self.proxy, 'node.avgNormX', -11.0)
        set_proxy_value(self.proxy, 'node.avgNormY', -7.0)
        self.assertEqual(self.controller.widget.pos_x, -11.0)
        self.assertEqual(self.controller.widget.pos_y, -7.0)
