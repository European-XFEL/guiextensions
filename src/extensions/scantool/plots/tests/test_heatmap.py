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
Y_ARRAY = np.linspace(START_POS[0], STOP_POS[0], SHAPE[0])
Z_ARRAY = np.random.randint(10, size=LENGTH)


class TestHeatmapSubplot(GuiTestCase):

    def setUp(self):
        super(TestHeatmapSubplot, self).setUp()
        self._plot = HeatmapPlot()

    def _setup_plot(self):
        # Populate the plot by specifying x_data and y_data
        self._x_data = Motor(name="x_data",
                             step=STEPS[1],
                             start_position=START_POS[1],
                             stop_position=STOP_POS[1])
        self._y_data = Motor(name="y_data",
                             step=STEPS[0],
                             start_position=START_POS[0],
                             stop_position=STOP_POS[0])
        self._z_data = DataSource(name="z_data")

        for device in (self._x_data, self._y_data, self._z_data):
            device.new_data(SHAPE)

        config = {X_DATA: self._x_data,
                  Y_DATA: self._y_data,
                  Z_DATA: self._z_data}
        self._plot.add(config, update=False)

    def test_init(self):
        self._setup_plot()
        image_data = self._plot.widget.plotItem.image

        # Check if the default image is empty and with the expected dimensions
        np.testing.assert_array_equal(image_data.shape, SHAPE)
        self.assertTrue((image_data == 0).all())

        x_axis, y_axis = self._plot.widget.plotItem.transformed_axes
        np.testing.assert_array_equal(X_ARRAY, x_axis)
        np.testing.assert_array_equal(Y_ARRAY, y_axis)

    def test_update(self):
        """Checks for the integrity of the `update` method by comparing the
           resulting widget image data wrt device data for every update"""

        # test full update
        self._assert_update(index_start=0)

        # test partial update
        self._assert_update(index_start=5)

    def _assert_update(self, index_start):
        self._setup_plot()

        devices = [self._x_data, self._y_data, self._z_data]
        x_repeated = np.tile(X_ARRAY, SHAPE[0])
        y_repeated = np.tile(Y_ARRAY, SHAPE[1])
        arrays = [x_repeated, y_repeated, Z_ARRAY]

        for index in range(index_start, LENGTH):
            # Set current_index for every iteration
            current_index = divmod(index, SHAPE[1])

            # Update device values
            for device, array in zip(devices, arrays):
                device.add(array[index], current_index)
                self._plot.update(device)

            # Check resulting image
            self._assert_image(current_index)

    def _assert_image(self, current_index):
        """Assert image widget data with the z_device data"""
        image = self._plot.widget.plotItem.image
        current_row = current_index[0] + 1

        # Check image shape
        image_shape = (current_row, SHAPE[1])
        self.assertEqual(image.shape, image_shape)

        # Check image data
        data = np.copy(self._z_data.data[:current_row])
        data[np.isnan(data)] = np.nanmin(data)
        np.testing.assert_array_equal(image, data)
