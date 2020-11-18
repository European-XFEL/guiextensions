from karabo.middlelayer import (
    Configurable, Float, VectorFloat, VectorChar, Node, AccessMode, Hash)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

from ..point_and_click import PointAndClick


class PnCNode(Configurable):
    displayType = 'WidgetNode|Point-and-Click'
    image = VectorChar(accessMode=AccessMode.READONLY)
    x = VectorFloat(accessMode=AccessMode.READONLY)
    y = VectorFloat(accessMode=AccessMode.READONLY)
    cross_x = Float()
    cross_y = Float()

class Object(Configurable):
    node = Node(PnCNode)

class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = PointAndClick(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):
        set_proxy_hash(
            self.proxy,
            Hash('node.cross_x', 48, 'node.cross_y', 1830,
                 'node.image', b'P1 2 2 1 0 0 1',
                 'node.x', [1, 2, 3], 'node.y', [4, 5, 6]))
        self.assertEqual(self.controller.widget.cross_x, 48)
        self.assertEqual(self.controller.widget.cross_y, 1830)
        self.assertEqual(self.controller.widget.image.pixel(1, 1), 0xff000000)
        self.assertEqual(self.controller.widget.crosses,
                         [(1, 4), (2, 5), (3, 6)])
