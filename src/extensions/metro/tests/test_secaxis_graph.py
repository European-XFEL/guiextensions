from pytest import approx

from extensions.metro.secaxis_graph import MetroSecAxisGraph
from karabo.native import Configurable, Float, Hash, Node, VectorDouble
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class VectorOutput(Configurable):
    x = VectorDouble()
    y0 = VectorDouble()


class AggregatorNode(Configurable):
    t0 = Float()
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
        assert secaxis._offset == 0

        vline = self.controller._vline
        assert vline.item.value() == 0
        assert not vline.item.isVisible()

        action = self._get_controller_action("Show vertical line")
        assert not action.isChecked()

    def test_vline_value(self):
        # Get the action
        set_proxy_hash(self.proxy, Hash('node.t0', 7.57))
        vline = self.controller._vline
        assert vline.item.value() == 7.57
        assert not vline.item.isVisible()

        secaxis = self.controller._secaxis
        assert secaxis._offset == approx(50.46, rel=1e-3)
        assert secaxis._step == approx(-6.67, rel=1e-3)

    def test_vline_visibility(self):
        action = self._get_controller_action("Show vertical line")
        action.trigger()
        assert action.isChecked()

        set_proxy_hash(self.proxy, Hash('node.t0', 7.57))
        vline = self.controller._vline
        assert vline.item.value() == 7.57
        assert vline.item.isVisible()

        secaxis = self.controller._secaxis
        assert secaxis._offset == approx(50.46, rel=1e-3)
        assert secaxis._step == approx(-6.67, rel=1e-3)

    # ---------------------------------------------------------------------
    # Helpers

    @property
    def widget(self):
        return self.controller.widget

    @property
    def model(self):
        return self.controller.model

    def _get_controller_action(self, text):
        # Get the x-transformation action
        for action in self.controller.widget.actions():
            if action.text() == text:
                return action
