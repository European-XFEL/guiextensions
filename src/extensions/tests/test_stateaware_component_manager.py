from karabo.native import Configurable, Hash, Node, VectorString
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_hash

from ..stateaware_component_manager import StateAwareComponentManager


class SACNode(Configurable):
    displayType = 'WidgetNode|StateAwareComponentManagerView'
    groups = VectorString()
    devices = VectorString()


class Object(Configurable):
    selectionList = Node(SACNode)


class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_property_proxy(schema, 'selectionList')
        self.controller = StateAwareComponentManager(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):
        groups = ['FooDevice:UNKNOWN:undefined:undefined:UNKNOWN:undefined:UNKNOWN:False',  # noqa
                  'BarDevice:NORMAL:undefined:undefined:NORMAL:undefined:NORMAL:False'  # noqa
                 ]
        set_proxy_hash(
            self.proxy,
            Hash('selectionList.groups', groups))
        model = self.controller._item_model

        self.assertEqual(model.data(model.index(0, 0)), "FooDevice")
        self.assertEqual(model.data(model.index(1, 0)), "BarDevice")

