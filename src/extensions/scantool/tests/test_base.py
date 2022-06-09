from unittest import skip

import numpy as np
from qtpy.QtWidgets import QWidget
from traits.api import Bool

from karabogui.testing import GuiTestCase

from ..const import SCAN_TYPE, X_DATA, Y_DATA
from ..controller import ScanController
from ..plots.base import BasePlot
from ..plots.multicurve import MultiCurvePlot
from .confs import ASCAN_CONFIG


class _BaseMockSubplot(BasePlot):

    cleared = Bool(False)
    destroyed = Bool(False)

    def __init__(self, parent=None):
        super(_BaseMockSubplot, self).__init__()
        self.widget = QWidget(parent)

    def clear(self):
        super(_BaseMockSubplot, self).clear()
        self.cleared = True

    def destroy(self):
        super(_BaseMockSubplot, self).destroy()
        self.destroyed = True

    def reset(self):
        self.reset_traits(["cleared", "destroyed"])


class MockSubplot(_BaseMockSubplot):
    """Placeholder for mock subplot"""


class AnotherMockSubplot(_BaseMockSubplot):
    """Placeholder for another mock subplot"""


class TestBaseWidgetController(GuiTestCase):

    def setUp(self):
        super(TestBaseWidgetController, self).setUp()
        self._scan_controller = ScanController()
        self._current_plot = None

    def test_basics(self):
        init_scan = self._scan_controller.scan
        self.assertIsNotNone(init_scan)

        new_scan = self._scan_controller.new_scan(ASCAN_CONFIG)
        self.assertIsNotNone(new_scan)
        self.assertNotEqual(init_scan, new_scan)
        self.assertEqual(new_scan.scan_type, ASCAN_CONFIG[SCAN_TYPE])

    @skip(reason="Usage of other classes for plots is not compatible with "
                 "new implementation")
    def test_use_plot(self):
        self._scan_controller.new_scan(ASCAN_CONFIG)
        self.assertIsNone(self._scan_controller._current_plot)

        # 1. Use MockSubplot
        self._current_plot = self._scan_controller._use_plot(MockSubplot)

        # 2. Use MockSubplot
        self._assert_mocked_subplot(MockSubplot, cleared=True, changed=False)

        # 3. Use AnotherMockSubplot again
        self._assert_mocked_subplot(AnotherMockSubplot,
                                    cleared=False, changed=True)

    def _assert_mocked_subplot(self, klass, cleared, changed):
        self._scan_controller._use_plot(klass)
        self.assertTrue(isinstance(self._scan_controller._current_plot, klass))

        # 1. Check if current plot is changed
        assert_changed = self.assertNotEqual if changed else self.assertEqual
        assert_changed(self._current_plot, self._scan_controller._current_plot)

        # 2. Check if current plot is destroyed
        assert_destroyed = self.assertTrue if changed else self.assertFalse
        assert_destroyed(self._current_plot.destroyed)

        # 3. Check if cleared
        assert_cleared = self.assertTrue if cleared else self.assertFalse
        assert_cleared(self._current_plot.cleared)

        self._current_plot = self._scan_controller._current_plot
        self._current_plot.reset()

    def test_use_multicurve_plot(self):
        # Setup
        self._scan_controller.new_scan(ASCAN_CONFIG)
        self._current_plot = self._scan_controller.use_multicurve_plot()

        # Check if current plot is as expected
        is_used = isinstance(self._scan_controller._current_plot,
                             MultiCurvePlot)
        self.assertTrue(is_used)

        # Check init
        self._assert_multicurve_init()

    def _multicurve_config(self):
        # Setup initial plot by using pos0 as x_data and others as y_data
        sources = self._scan_controller.scan._data_sources

        # Populate the plot by specifying x_data and y_data
        x_data = self._scan_controller.scan._motors[0]
        return [{X_DATA: x_data, Y_DATA: y_data} for y_data in sources]

    def _assert_multicurve_init(self):
        # Check init
        plot_items = self._current_plot._items._items
        plotItem = self._current_plot.widget.plotItem
        expected_config = self._multicurve_config()

        num_data = len(expected_config)
        self.assertEqual(len(plot_items), num_data)

        for item, plot_config in plot_items.items():
            self.assertTrue(plot_config in expected_config)
            self.assertTrue(item in plotItem.dataItems)
            np.testing.assert_array_equal(item.xData, [])
            np.testing.assert_array_equal(item.yData, [])
