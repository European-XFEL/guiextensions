from contextlib import contextmanager
from unittest import mock

import numpy as np

from karabo.native import Configurable, Hash, Node, VectorDouble
from karabogui.testing import (
    get_class_property_proxy, GuiTestCase, set_proxy_hash)
from extensions.metro.secaxis_graph import MetroSecAxisGraph


class VectorOutput(Configurable):
    x = VectorDouble()
    y0 = VectorDouble()


class AggregatorNode(Configurable):
    outputVector = Node(VectorOutput)


class Object(Configurable):
    node = Node(AggregatorNode)


class TestSecAxisGraph(GuiTestCase):
    def setUp(self):
        super(TestSecAxisGraph, self).setUp()
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = MetroSecAxisGraph(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_basics(self):
        secaxis = self.controller._secaxis
        assert secaxis._offset == 50.45
        assert secaxis._step == 6.667

        vline = self.controller._vline
        assert vline.value() == -7.5675
        assert not vline.isVisible()

    def test_x2_transform(self):
        # Get the action
        action = self._get_controller_action("X2-Transformation")
        self.assertIsNotNone(action)

        offset, step = 3, 2
        # Trigger the transformation configuration
        content = {"x2_offset": offset, "x2_step": step}
        with mock.patch("extensions.metro.secaxis_graph.X2TransformDialog.get",
                        return_value=(content, True)):
            action.trigger()

        secaxis = self.controller._secaxis
        assert secaxis._offset == offset
        assert secaxis._step == step
        assert self.model.x2_offset == offset
        assert self.model.x2_step == step

    def test_vline(self):
        # Get the action
        action = self._get_controller_action("Vertical Line")
        self.assertIsNotNone(action)

        # Trigger the transformation configuration
        value, visible = 6, True
        content = {"vline_value": value, "vline_visible": visible}
        with mock.patch("extensions.metro.secaxis_graph.VLineDialog.get",
                        return_value=(content, True)):
            action.trigger()

        vline = self.controller._vline
        assert vline.value() == value
        assert vline.isVisible() == visible
        assert self.model.vline_value == value
        assert self.model.vline_visible == visible

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
    def model(self):
        return self.controller.model

    @property
    def plot_data(self):
        controller = self.controller
        return {'outputStd': controller._std_plot,
                'outputIo': controller._intensity_plot,
                'outputCounts': controller._counts_plot}

    def _get_controller_action(self, text):
        # Get the x-transformation action
        for action in self.controller.widget.actions():
            if action.text() == text:
                return action
