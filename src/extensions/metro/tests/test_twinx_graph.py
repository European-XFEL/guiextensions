import numpy as np

from extensions.metro.twinx_graph import MetroTwinXGraph
from karabo.native import Configurable, Hash, Node, VectorDouble
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class VectorOutput(Configurable):
    x = VectorDouble()
    y0 = VectorDouble()


class AggregatorNode(Configurable):
    dXAS = Node(VectorOutput)
    XASn = Node(VectorOutput)
    XASp = Node(VectorOutput)


class Object(Configurable):
    node = Node(AggregatorNode)


class TestTwinXGraph(GuiTestCase):
    def setUp(self):
        super(TestTwinXGraph, self).setUp()
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = MetroTwinXGraph(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_basics(self):
        legend = self.controller._legend
        assert len(legend.items) == 3

        for plot in self.controller._plots:
            assert plot.path == legend.getLabel(plot.item).text

    def test_values(self):
        values = {
            'dXAS': (np.random.random(300), np.random.random(300)),
            'XASn': (np.random.random(300), np.random.random(300)),
            'XASp': (np.random.random(300), np.random.random(300))
        }
        self.update_proxy(**values)

        for plot in self.controller._plots:
            exp_x, exp_y = values[plot.path]
            act_x, act_y = plot.item.getData()
            np.testing.assert_array_equal(act_x, exp_x)
            np.testing.assert_array_equal(act_y, exp_y)

    # ---------------------------------------------------------------------
    # Helpers

    def update_proxy(self, **kwargs):
        flattened = {}
        for key, (x, y) in kwargs.items():
            flattened[f'node.{key}.x'] = x
            flattened[f'node.{key}.y0'] = y
        set_proxy_hash(self.proxy, Hash(flattened))

    @property
    def widget(self):
        return self.controller.widget
