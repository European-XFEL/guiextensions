import numpy as np

from extensions.display_xas_graph import DisplayXasGraph
from karabo.native import Configurable, Hash, Node, VectorDouble
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class DataNode(Configurable):
    bins = VectorDouble()
    absorption = VectorDouble()
    intensity = VectorDouble()
    counts = VectorDouble()


class ChannelNode(Configurable):
    data = Node(DataNode)


class TestXasGraph(GuiTestCase):
    def setUp(self):
        super(TestXasGraph, self).setUp()
        schema = ChannelNode.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'data')
        self.controller = DisplayXasGraph(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_basics(self):
        for plot in self.controller.plots.values():
            x, y = plot.getData()
            np.testing.assert_array_equal(x, [])
            np.testing.assert_array_equal(y, [])

    def test_value_update(self):
        values = {
            'bins': np.arange(300),
            'absorption': np.random.random(300),
            'intensity': np.random.random(300),
            'counts': np.random.random(300),
        }

        set_proxy_hash(self.proxy, Hash('data', Hash(values)))

        for name, plot in self.controller.plots.items():
            exp_y = values[name]
            act_x, act_y = plot.getData()
            np.testing.assert_array_equal(act_x, values['bins'])
            np.testing.assert_array_equal(act_y, exp_y)
