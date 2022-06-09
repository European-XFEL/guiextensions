import numpy as np

from karabogui.testing import GuiTestCase

from ...const import X_DATA, Y_DATA
from ...data.device import Device
from ..multicurve import MultiCurvePlot

LENGTH = 10
X_ARRAY = np.linspace(6, 15, 10)
Y_ARRAY = np.random.randint(10, size=LENGTH)
Z_ARRAY = np.random.randint(10, size=LENGTH)


class TestMultiCurveController(GuiTestCase):

    def setUp(self):
        super(TestMultiCurveController, self).setUp()
        self._plot = MultiCurvePlot()

        # Populate the plot by specifying x_data and y_data
        self._x_data = Device(
            name="x_data",
            device_id="TEST/DEVICE/X",
            _data=np.full(LENGTH, np.nan))
        self._y_data = Device(
            name="y_data",
            device_id="TEST/DEVICE/Y",
            _data=np.full(LENGTH, np.nan))
        self._z_data = Device(
            name="z_data",
            device_id="TEST/DEVICE/Z",
            _data=np.full(LENGTH, np.nan))

        self._add_data_to_plot()

    def _add_data_to_plot(self):
        self._configs = []
        for y_data in (self._y_data, self._z_data):
            config = {X_DATA: self._x_data, Y_DATA: y_data}
            self._plot.add(config, update=False)
            self._configs.append(config)

    def test_init(self):
        plot_items = self._plot._items._items
        self.assertEqual(len(plot_items), len(self._configs))

        for item, plot_config in plot_items.items():
            self.assertTrue(plot_config in self._configs)
            np.testing.assert_array_equal(item.xData, [None])
            np.testing.assert_array_equal(item.yData, [None])

    def test_update(self):
        devices = [self._x_data, self._y_data, self._z_data]
        arrays = [X_ARRAY, Y_ARRAY, Z_ARRAY]

        for index in range(LENGTH):
            # Set data
            for device, array in zip(devices, arrays):
                device.add(X_ARRAY[index], [index])
                self._plot.update(device)

            # Assert data
            for y_device in [self._y_data, self._z_data]:
                config = {X_DATA: self._x_data, Y_DATA: y_device}
                item = self._plot._items.get_item_by_config(config)
                self.assertIsNotNone(item)

                x_data = self._x_data.data[:index + 1]
                y_data = y_device.data[:index + 1]
                # Account for mocked line plot for single point data
                if index == 0:
                    x_data = np.repeat(x_data, 2)
                    y_data = np.repeat(y_data, 2)
                np.testing.assert_array_equal(item.xData, x_data)
                np.testing.assert_array_equal(item.yData, y_data)

    def test_clear(self):
        self._plot.clear()

        # Check if plots are items are cleared
        plot_items = self._plot._items._items
        self.assertEqual(len(plot_items), 0)

        # Then add items
        self._add_data_to_plot()

        # Then check again
        has_curves = len(plot_items) == len(self._configs) == 2
        self.assertTrue(has_curves)
