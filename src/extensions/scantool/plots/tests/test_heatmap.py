import numpy as np

from karabogui.testing import GuiTestCase

from ..heatmap import HeatmapPlot
from ...const import X_DATA, Y_DATA, Z_DATA
from ...data.device import Motor, DataSource

START_POS = np.array([2, 3])
STOP_POS = np.array([4, 6])
STEPS = [2, 3]
SHAPE = np.add(STEPS, 1)
LENGTH = np.prod(SHAPE)
X_ARRAY = np.linspace(START_POS[1], STOP_POS[1], SHAPE[1])
X_OFFSET = (X_ARRAY[1] - X_ARRAY[0]) / 2
Y_ARRAY = np.linspace(START_POS[0], STOP_POS[0], SHAPE[0])
Y_OFFSET = (Y_ARRAY[1] - Y_ARRAY[0]) / 2
Z_ARRAY = np.arange(LENGTH)


class TestHeatmapSubplot(GuiTestCase):

    def setUp(self):
        super(TestHeatmapSubplot, self).setUp()
        self._plot = HeatmapPlot()

    def _setup_plot(self, transpose=False, x_reverse=False, y_reverse=False):
        # Populate the plot by specifying x_data and y_data
        y_start, x_start = START_POS
        y_stop, x_stop = STOP_POS

        if x_reverse:
            x_stop, x_start = x_start, x_stop
        if y_reverse:
            y_stop, y_start = y_start, y_stop

        self._x_data = Motor(name="pos1",
                             step=STEPS[1],
                             start_position=x_start,
                             stop_position=x_stop)
        self._y_data = Motor(name="pos0",
                             step=STEPS[0],
                             start_position=y_start,
                             stop_position=y_stop)
        self._z_data = DataSource(name="y1")

        for device in (self._x_data, self._y_data, self._z_data):
            device.new_data(SHAPE)

        x_data, y_data = self._x_data, self._y_data
        if transpose:
            x_data, y_data = y_data, x_data

        config = {X_DATA: x_data,
                  Y_DATA: y_data,
                  Z_DATA: self._z_data}
        self._plot.add(config, update=False)

    def test_init(self):
        self._setup_plot()
        image_data = self._plot.widget.plotItem.image

        # Check if the default image is empty and with the expected dimensions
        np.testing.assert_array_equal(image_data.shape, SHAPE)
        self.assertTrue((image_data == 0).all())

        # Check if image dimensions is equal to axis values
        x_axis, y_axis = self._plot.widget.plotItem.transformed_axes
        np.testing.assert_array_equal(X_ARRAY - X_OFFSET, x_axis)
        np.testing.assert_array_equal(Y_ARRAY - Y_OFFSET, y_axis)

    def test_update(self):
        """Checks for the integrity of the `update` method by comparing the
           resulting widget image data wrt device data for every update"""

        # test full update
        self._assert_update()
        self._assert_update(x_reverse=True)
        self._assert_update(y_reverse=True)
        self._assert_update(x_reverse=True, y_reverse=True)

        # test partial update
        self._assert_update(index_start=5)
        self._assert_update(index_start=5, x_reverse=True)
        self._assert_update(index_start=5, y_reverse=True)
        self._assert_update(index_start=5, x_reverse=True, y_reverse=True)

        # test with inverse
        self._assert_update(transpose=True)
        self._assert_update(transpose=True, x_reverse=True)
        self._assert_update(transpose=True, y_reverse=True)
        self._assert_update(transpose=True, x_reverse=True, y_reverse=True)

    def _assert_update(self, index_start=0, transpose=False,
                       x_reverse=False, y_reverse=False):
        self._setup_plot(transpose, x_reverse, y_reverse)

        # Setup device data
        x_array, y_array = self._get_xy_device_data(
            transpose, x_reverse, y_reverse)
        y_shape, x_shape = SHAPE
        if transpose:
            y_shape, x_shape = x_shape, y_shape

        x_repeated = np.tile(x_array, y_shape)
        y_repeated = np.tile(y_array, x_shape)
        arrays = [x_repeated, y_repeated, Z_ARRAY]
        devices = [self._x_data, self._y_data, self._z_data]

        for index in range(index_start, LENGTH):
            # Set current_index for every iteration
            current_index = divmod(index, SHAPE[1])

            # Update device values
            for device, array in zip(devices, arrays):
                device.add(array[index], current_index)
                self._plot.update(device)

            # Check resulting image
            self._assert_image(current_index, transpose, x_reverse, y_reverse)

    def _get_xy_device_data(self, transpose, x_reverse=False, y_reverse=False):
        x_array, y_array = X_ARRAY, Y_ARRAY
        if x_reverse:
            x_array = x_array[::-1]
        if y_reverse:
            y_array = y_array[::-1]
        if transpose:
            x_array, y_array = y_array, x_array

        return x_array, y_array

    def _assert_image(self, current_index, transpose, x_reverse, y_reverse):
        """Assert image widget data with the z_device data"""
        image = self._plot.widget.plotItem.image
        current_row = current_index[0] + 1

        # # Check image shape
        image_shape = (current_row, SHAPE[1])
        if transpose:
            image_shape = image_shape[::-1]
        self.assertEqual(image.shape, image_shape)

        # Check image data
        data = np.copy(self._z_data.data[:current_row])
        data[np.isnan(data)] = np.nanmin(data)
        if x_reverse:
            data = np.fliplr(data)
        if y_reverse:
            data = np.flipud(data)
        if transpose:
            data = data.T
        np.testing.assert_array_equal(image, data)

        # Get displayed xy values
        x_array, y_array = self._get_xy_device_data(
            transpose, x_reverse, y_reverse)
        x_array = np.sort(x_array[:image_shape[1]])
        y_array = np.sort(y_array[:image_shape[0]])

        # Check image dimensions
        x_axis, y_axis = self._plot.widget.plotItem.transformed_axes
        np.testing.assert_array_equal(x_array - X_OFFSET, x_axis)
        np.testing.assert_array_equal(y_array - Y_OFFSET, y_axis)
