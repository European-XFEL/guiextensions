import numpy as np

from extensions.display_trigger_slice_graph import TriggerSliceGraph
from karabo.native import (
    Configurable, Hash, Node, VectorBool, VectorDouble, VectorInt64)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class PreviewOutputNode(Configurable):
    start = VectorInt64()
    stop = VectorInt64()
    fel = VectorBool()
    ppl = VectorBool()
    data = VectorDouble()


class PretendChannelNode(Configurable):
    schema = Node(PreviewOutputNode)


class TestTriggerSliceGraph(GuiTestCase):
    def setUp(self):
        super().setUp()
        schema = PretendChannelNode.getClassSchema()
        self.proxy = get_class_property_proxy(schema, "schema")
        self.controller = TriggerSliceGraph(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_empty(self):
        np.testing.assert_array_equal(
            self.controller._curve_item.getData(), [None, None])
        assert self.controller._trigger_regions == []

    def test_value_update(self):
        starts = np.arange(0, 200, 4, dtype=int)
        stops = starts + 3
        fel = np.zeros_like(starts, dtype=bool)
        fel[10:20] = True
        ppl = np.zeros_like(starts, dtype=bool)
        ppl[15:25] = True
        data = np.random.random(size=250)
        set_proxy_hash(
            self.proxy,
            Hash("schema",
                 Hash("start", starts,
                      "stop", stops,
                      "fel", fel,
                      "ppl", ppl,
                      "data", data)))
        np.testing.assert_array_equal(
            self.controller._curve_item.getData(),
            [np.arange(data.size), data])

        assert len(self.controller._trigger_regions) == starts.size
        for start, stop, region in zip(starts, stops,
                                       self.controller._trigger_regions):
            assert region.getRegion() == (start, stop)
