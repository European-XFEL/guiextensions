from contextlib import contextmanager

import numpy as np

from extensions.metro.xas_graph import MetroXasGraph
from karabo.native import Configurable, Hash, Node, VectorDouble
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class VectorOutput(Configurable):
    x = VectorDouble()
    y0 = VectorDouble()


class AggregatorNode(Configurable):
    outputStd = Node(VectorOutput)
    outputIo = Node(VectorOutput)
    outputCounts = Node(VectorOutput)


class Object(Configurable):
    node = Node(AggregatorNode)


class TestXasGraph(GuiTestCase):
    def setUp(self):
        super(TestXasGraph, self).setUp()
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = MetroXasGraph(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_basics(self):
        for name, plot in self.plot_data.items():
            assert plot.path == name
            assert plot.item is not None
            x, y = plot.item.getData()
            np.testing.assert_array_equal(x, [])
            np.testing.assert_array_equal(y, [])

    def test_value_update(self):
        values = {
            'outputStd': (np.random.random(300), np.random.random(300)),
            'outputIo': (np.random.random(300), np.random.random(300)),
            'outputCounts': (np.random.random(300), np.random.random(300))
        }
        self.update_proxy(**values)

        for name, plot in self.plot_data.items():
            exp_x, exp_y = values[name]
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

    @property
    def plot_data(self):
        controller = self.controller
        return {'outputStd': controller._std_plot,
                'outputIo': controller._intensity_plot,
                'outputCounts': controller._counts_plot}
