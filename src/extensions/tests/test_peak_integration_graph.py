import numpy as np
from numpy.testing import assert_array_equal

from extensions.peak_integration_graph import (
    NUM_PEAKS, DisplayPeakIntegrationGraph)
from extensions.utils import get_ndarray_hash_from_data
from karabo.native import (
    Configurable, Hash, NDArray, Node, UInt16, VectorInt32, VectorUInt32)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

DEFAULT_VALUES = dict(
    peakPositions=np.arange(0, 30, 3),
    peakWidths=np.array([-1, 1]),
    peakBaseline=np.array([-2, -1])
)


class PeakIntegrationNode(Configurable):
    peakPositions = VectorUInt32()
    peakWidths = VectorInt32()
    peakBaseline = VectorInt32()


class Device(Configurable):
    node = Node(PeakIntegrationNode)
    trace = NDArray(
        dtype=UInt16,
        shape=(40,)
    )


class TestPeakIntegrationGraph(GuiTestCase):
    def setUp(self):
        super(TestPeakIntegrationGraph, self).setUp()
        schema = Device.getClassSchema()

        self.peak_proxy = proxy = get_class_property_proxy(schema, 'node')
        set_proxy_hash(proxy, Hash('node', Hash(DEFAULT_VALUES)))

        self.controller = DisplayPeakIntegrationGraph(proxy=proxy)
        self.controller.create(None)

        self.trace_proxy = get_class_property_proxy(schema, 'trace')
        self.controller.visualize_additional_property(self.trace_proxy)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_basics(self):
        controller = self.controller

        # Check peak region items
        assert len(controller._peak_regions) == NUM_PEAKS
        assert len(controller._peak_lines) == NUM_PEAKS
        assert len(controller._base_regions) == NUM_PEAKS

        # Check peak region data
        assert_array_equal(controller._peak_positions, np.arange(0, 30, 3))
        assert_array_equal(controller._peak_widths, [-1, 1])
        assert_array_equal(controller._peak_baseline, [-2, -1])

        # Check peak region visibility
        for item in controller.region_items:
            assert item.isVisible() is False

        # Check trace and markers
        assert controller._curve_item.xData is None
        assert controller._curve_item.yData is None

        peak_x, peak_y = controller._peak_item.getData()
        assert_array_equal(peak_x, [])
        assert_array_equal(peak_y, [])

    def test_update_position(self):
        # Reset controller monitor
        controller = self.controller
        controller.reset_traits(['_peak_region_updated',
                                 '_base_region_updated'])
        assert controller._peak_region_updated is False
        assert controller._base_region_updated is False

        # Update node value
        values = DEFAULT_VALUES.copy()
        values['peakPositions'] = np.arange(0, 30, 3) + 2  # shift by 2
        set_proxy_hash(self.peak_proxy, Hash('node', Hash(values)))

        # Check changes
        assert controller._peak_region_updated is True
        assert controller._base_region_updated is True

    def test_update_peak_widths(self):
        # Reset controller monitor
        controller = self.controller
        controller.reset_traits(['_peak_region_updated',
                                 '_base_region_updated'])
        assert controller._peak_region_updated is False
        assert controller._base_region_updated is False

        # Update node value
        values = DEFAULT_VALUES.copy()
        values['peakWidths'] = np.array([-2, 2])
        set_proxy_hash(self.peak_proxy, Hash('node', Hash(values)))

        # Check changes
        assert controller._peak_region_updated is True
        assert controller._base_region_updated is False

    def test_update_peak_baseline(self):
        # Reset controller monitor
        controller = self.controller
        controller.reset_traits(['_peak_region_updated',
                                 '_base_region_updated'])
        assert controller._peak_region_updated is False
        assert controller._base_region_updated is False

        # Update node value
        values = DEFAULT_VALUES.copy()
        values['peakBaseline'] = np.array([-3, -2])
        set_proxy_hash(self.peak_proxy, Hash('node', Hash(values)))

        # Check changes
        assert controller._peak_region_updated is False
        assert controller._base_region_updated is True

    def test_update_trace(self):
        controller = self.controller

        trace = np.arange(40) * 2
        set_proxy_hash(self.trace_proxy,
                       Hash('trace', get_ndarray_hash_from_data(trace)))

        # Check peak region items
        assert len(controller._peak_regions) == NUM_PEAKS
        assert len(controller._peak_lines) == NUM_PEAKS
        assert len(controller._base_regions) == NUM_PEAKS

        # Check peak region data
        assert_array_equal(controller._peak_positions, np.arange(0, 30, 3))
        assert_array_equal(controller._peak_widths, [-1, 1])
        assert_array_equal(controller._peak_baseline, [-2, -1])

        # Check peak region visibility
        for item in controller.region_items:
            assert item.isVisible() is True

        # Check trace and markers
        assert_array_equal(controller._curve_item.xData, np.arange(trace.size))
        assert_array_equal(controller._curve_item.yData, trace)

        peak_x, peak_y = controller._peak_item.getData()
        assert_array_equal(peak_x, DEFAULT_VALUES['peakPositions'])
        assert_array_equal(peak_y, trace[DEFAULT_VALUES['peakPositions']])
