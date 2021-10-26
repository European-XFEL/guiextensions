from extensions.display_ipm_quadrant import DisplayIPMQuadrant
from karabo.native import Configurable, Float, Hash, Node
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class DataNode(Configurable):
    displayType = "WidgetNode|IPM-Quadrant"
    posX = Float(defaultValue=0.1)
    posY = Float(defaultValue=-0.7)
    intensity = Float(defaultValue=-2000)


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
        set_proxy_hash(self.proxy, Hash('node.posX', -0.2, 'node.posY', -0.7,
                                        'node.intensity', -2000.0))
        self.assertEqual(self.controller.widget.pos_x, -0.2)
        self.assertEqual(self.controller.widget.pos_y, -0.7)
        self.assertEqual(self.controller.widget.intensity, -2000)

    def test_values_oob(self):
        set_proxy_hash(self.proxy, Hash('node.posX', -1.2, 'node.posY', 1.7,
                                        'node.intensity', -2000.0))
        self.assertEqual(self.controller.widget.pos_x, -1.0)
        self.assertEqual(self.controller.widget.pos_y, 1.0)
        self.assertEqual(self.controller.widget.intensity, -2000)
