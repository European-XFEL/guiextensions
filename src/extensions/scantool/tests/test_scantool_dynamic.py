import numpy as np

from extensions.scantool.plots.heatmap import HeatmapPlot
from extensions.scantool.plots.multicurve import MultiCurvePlot
from extensions.scantool.tests.confs import (
    A2SCAN_CONFIG, ASCAN_CONFIG, C2SCAN_CONFIG, MESH_CONFIG)

try:
    from karabogui.binding.api import ProxyStatus
except ImportError:
    # compatibility with GUI version < 2.16
    from karabo.common.api import ProxyStatus

from karabo.common.api import State
from karabo.native import (
    AccessMode, Configurable, Double, Hash, Node, String, UInt32, VectorDouble,
    VectorInt32, VectorString)
from karabogui.binding.api import (
    DeviceClassProxy, PropertyProxy, apply_configuration, build_binding)
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_value

from ..const import (
    ACTUAL_STEP, CURRENT_INDEX, MESHES, MOTOR_IDS, MOTOR_NAMES, MOTORS,
    NR_MOTORS, NR_VALUES, SCAN_TYPE, SOURCE_IDS, SOURCE_NAMES, SOURCES,
    START_POSITIONS, STEPS, STOP_POSITIONS, X_DATA, Y_DATA, Z_DATA)
from ..display_scantool_dynamic import (
    HISTORY_PROXY_PATH, ScantoolDynamicWidget)

MAX_OUTPUT_POINTS = 100


class DataNode(Configurable):
    # Data node represent actual karabacon output schema

    displayType = "WidgetNode|Scantool-Base"

    # Scan settings
    scanType = String(
        defaultValue="ascan",
        accessMode=AccessMode.READONLY)
    numDataSources = UInt32(
        defaultValue=1,
        accessMode=AccessMode.READONLY)
    steps = VectorInt32(
        defaultValue=[5],
        accessMode=AccessMode.READONLY)
    actualStep = UInt32(
        defaultValue=0,
        accessMode=AccessMode.READONLY)
    currentIndex = VectorInt32(
        defaultValue=[0],
        accessMode=AccessMode.READONLY)

    # Motor positions
    startPositions = VectorDouble(
        accessMode=AccessMode.READONLY,
        defaultValue=[0.])
    stopPositions = VectorDouble(
        accessMode=AccessMode.READONLY,
        defaultValue=[1.])

    # Motor and source values
    for index in range(NR_MOTORS):
        locals()[f'pos{index}'] = Double(
            defaultValue=0.0,
            accessMode=AccessMode.READONLY)

    for index in range(NR_VALUES):
        locals()[f'y{index}'] = Double(
            defaultValue=0.0,
            accessMode=AccessMode.READONLY)

    motorIds = VectorString(
        displayedName="Motor IDs",
        description="Motor IDs",
        defaultValue=[],
        maxSize=NR_MOTORS,
        accessMode=AccessMode.READONLY)

    sourceIds = VectorString(
        displayedName="Data Source IDs",
        description="Data Source IDs",
        defaultValue=[],
        maxSize=NR_VALUES,
        accessMode=AccessMode.READONLY)


class HistoryNode(Configurable):
    displayType = "WidgetNode|Scantool-Base"

    scanType = String(
        defaultValue="ascan",
        accessMode=AccessMode.READONLY)

    steps = VectorInt32(
        defaultValue=[5],
        maxSize=16,
        accessMode=AccessMode.READONLY)

    startPositions = VectorDouble(
        accessMode=AccessMode.READONLY,
        defaultValue=[0.])
    stopPositions = VectorDouble(
        accessMode=AccessMode.READONLY,
        defaultValue=[1.])

    for index in range(NR_MOTORS):
        locals()[f'pos{index}'] = VectorDouble(
            maxSize=MAX_OUTPUT_POINTS,
            accessMode=AccessMode.READONLY)

    for index in range(NR_VALUES):
        locals()[f'y{index}'] = VectorDouble(
            maxSize=MAX_OUTPUT_POINTS,
            accessMode=AccessMode.READONLY)

    motorIds = VectorString(
        defaultValue=[],
        maxSize=NR_MOTORS,
        accessMode=AccessMode.READONLY)

    sourceIds = VectorString(
        maxSize=NR_VALUES,
        defaultValue=[],
        accessMode=AccessMode.READONLY)


class OutputSchema(Configurable):
    data = Node(DataNode)
    state = String(enum=State, displayType='State')


class HistoryDataNode(Configurable):
    data = Node(HistoryNode)


class HistorySchemaNode(Configurable):
    schema = Node(HistoryDataNode)


class HistoryOutputNode(Configurable):
    output = Node(HistorySchemaNode)


class HistoryOutputSchema(Configurable):
    history = Node(HistoryOutputNode)


class TestScantoolDynamicWidget(GuiTestCase):

    def setUp(self):
        super(TestScantoolDynamicWidget, self).setUp()

        schema = OutputSchema.getClassSchema()
        self.binding = build_binding(schema)
        device = DeviceClassProxy(binding=self.binding,
                                  server_id='KarabaconServer',
                                  status=ProxyStatus.ONLINE)
        self.proxy = PropertyProxy(root_proxy=device, path='data')

        schema = HistoryOutputSchema.getClassSchema()
        self.history_proxy = get_property_proxy(schema, HISTORY_PROXY_PATH)

        # Create the controllers and initialize their widgets
        self.controller = ScantoolDynamicWidget(proxy=self.proxy)
        self.controller.create(None)
        self.controller.visualize_additional_property(self.history_proxy)
        self.controller._first_proxy_received = True
        self._scan = None

    def tearDown(self):
        super(TestScantoolDynamicWidget, self).tearDown()
        self.controller.destroy()

    def test_init(self):
        # Setup scantool widget
        self.assertIsNone(self.controller._scan)

        # Set initial scan config
        config = ASCAN_CONFIG
        self._write_scan_config(config)

        # Set and check state
        set_proxy_value(self.proxy, 'state', 'ACQUIRING')
        self.assertEqual(self.controller._get_state(self.proxy), 'ACQUIRING')

        self._assert_scan_config(config)

        # Check setup device for ascan
        scan = self.controller._scan
        self.assertEqual(len(scan.motors), 1)
        self.assertEqual(len(scan.data_sources), 1)

        motor = scan._motors[0]
        self.assertEqual(motor.name, "pos0")
        self.assertTrue(np.isnan(motor.data).all())

        data_source = scan._data_sources[0]
        self.assertEqual(data_source.name, "y0")
        self.assertTrue(np.isnan(data_source.data).all())

    def test_first_acquire(self):
        # Set initial scan config
        set_proxy_value(self.proxy, 'state', 'ACQUIRING')
        self._write_scan_config(ASCAN_CONFIG)

        # Now change the device to acquiring, with only one update on the
        # device values
        config = Hash('data', Hash("pos0", 100,
                                   "y0", 200,
                                   ACTUAL_STEP, 0))
        apply_configuration(config, self.binding)
        scan = self.controller._scan
        # Check scan settings
        self.assertEqual(scan.actual_step, 0)

        # Check devices
        motor = scan._motors[0]
        self.assertEqual(motor.data[1], 100)

        data_source = scan._data_sources[0]
        self.assertEqual(data_source.data[1], 200)

    def test_full_ascan(self):
        # Do a full scan
        config = ASCAN_CONFIG
        self._write_full_scan(config)
        self._assert_full_scan(config)

    def test_full_mesh(self):
        # Do a full scan
        config = MESH_CONFIG
        self._write_full_scan(config)
        self._assert_full_scan(config)

    def test_full_cscan(self):
        config = C2SCAN_CONFIG
        self._write_full_scan(config)
        self._assert_full_scan(config)

    def test_second_ascan(self):
        # Do a full scan
        self._write_full_scan(MESH_CONFIG)

        # Now, do a second scan
        config = A2SCAN_CONFIG
        self._write_full_scan(config)
        self._assert_full_scan(config)

    def test_second_mesh(self):
        # Do a first full scan
        self._write_full_scan(ASCAN_CONFIG)

        # Now, do a second scan
        config = MESH_CONFIG
        self._write_full_scan(config)
        self._assert_full_scan(config)

    def test_history_plot(self):
        # Do a full scan
        config = ASCAN_CONFIG
        self._write_scan_history(config)
        self._assert_full_scan(config)
        self._assert_multicurve_plot(config)

    def test_multiple_plots(self):
        config = ASCAN_CONFIG
        self._write_scan_history(config)
        self.assertTrue(len(self._get_scans()) == 1)

        # Request to plot the same scan is rejected
        self._write_scan_history(config)
        self.assertTrue(len(self._get_scans()) == 1)

        # A single plot is identified by an uniques motor_id, source_id pair
        # We do not update plot if the scan is already plotted. This will never
        # happen, but lets test it
        config["y0"] = [3 * i for i in range(10)]
        self._write_scan_history(config)
        self.assertTrue(len(self._get_scans()) == 1)

        # Source id is different: add a new plot
        config["sourceIds"] = ["ascan_1:source"]
        self._write_scan_history(config)
        self.assertTrue(len(self._get_scans()) == 2)

        # We do not plot several scans if the motor ids do not match
        config["sourceIds"] = ["ascan_2:source"]
        config["motorIds"] = ["some_other_motor"]
        self._write_scan_history(config)
        self.assertTrue(len(self._get_scans()) == 1)

        # New realtime scan clears all plots
        config = ASCAN_CONFIG
        self._write_full_scan(config)
        self.assertTrue(len(self._get_scans()) == 1)

        # Realtime or historical mesh scan clears all plots
        config = MESH_CONFIG
        self._write_scan_history(config)
        self.assertTrue(len(self._get_scans()) == 1)

    # -----------------------------------------------------------------------
    # Helper methods

    def _write_scan_config(self, config):
        config = config.copy()
        active_motors = config.pop(MOTORS)
        for motor in MOTOR_NAMES:
            value = 0 if motor in active_motors else np.nan
            config[motor] = value

        active_sources = config.pop(SOURCES)
        for source in SOURCE_NAMES:
            value = 0 if source in active_sources else np.nan
            config[source] = value

        flat_config = [item for items in config.items() for item in items]
        config = Hash('data', Hash(*flat_config))
        apply_configuration(config, self.binding)

    def _write_full_scan(self, config):
        # Set initial scan config
        self._write_scan_config(config)
        set_proxy_value(self.proxy, 'state', 'ACQUIRING')

        # Now change the device to ACQUIRING, with 10 updates on the
        # device values
        total_steps = np.prod(np.add(config[STEPS], 1))
        for index in range(total_steps):
            steps = divmod(index, config[STEPS][-1] + 1)
            if config[SCAN_TYPE] not in MESHES:
                steps = (steps[1],)

            hash = Hash('data', Hash(
                ACTUAL_STEP, index,
                CURRENT_INDEX, steps,
                *self._motor_values(len(config[MOTORS]), index),
                *self._source_values(len(config[SOURCES]), index)))
            apply_configuration(hash, self.binding)

        # Note that the scan has finished, thus change the state to ON
        self._scan = self.controller._scan
        set_proxy_value(self.proxy, 'state', 'ON')

    def _write_scan_history(self, config):
        # Set initial scan config
        data = Hash(SCAN_TYPE, config[SCAN_TYPE],
                    STEPS, config[STEPS],
                    START_POSITIONS, config[START_POSITIONS],
                    STOP_POSITIONS, config[STOP_POSITIONS],
                    *self._motor_vector_values(
                        len(config[MOTOR_IDS]), config[STEPS][0]),
                    *self._source_vector_values(
                        len(config[SOURCE_IDS]), config[STEPS][0]),
                    MOTOR_IDS, config[MOTOR_IDS],
                    SOURCE_IDS, config[SOURCE_IDS],)
        apply_configuration(data, self.history_proxy.binding)
        self._scan = self._get_scans()[-1]

    def _motor_values(self, num_motors, actual_step):
        """Dummy motor values."""
        values = []
        for index in range(num_motors):
            values.extend([f"pos{index}", actual_step + index])
        return values

    def _source_values(self, num_sources, actual_step):
        """Dummy source values."""
        values = []
        for index in range(num_sources):
            values.extend([f"y{index}", (actual_step + index) ** 2])
        return values

    def _motor_vector_values(self, num_motors, total_steps):
        """Dummy motor vector values."""
        values = []
        for index in range(NR_MOTORS):
            if index <= num_motors - 1:
                values.extend([f"pos{index}", list(range(0, total_steps + 1))])
            else:
                values.extend([f"pos{index}", []])
        return values

    def _source_vector_values(self, num_sources, total_steps):
        """Dummy source vector values."""
        values = []
        for index in range(NR_VALUES):
            if index <= num_sources - 1:
                values.extend([f"y{index}",  [i*i for i in range(10)]])
            else:
                values.extend([f"y{index}", []])
        return values

    def _get_scans(self):
        return self.controller._controller.scans

    # -----------------------------------------------------------------------
    # Assert methods

    def _assert_scan_config(self, config):
        scan = self.controller._scan
        self.assertIsNotNone(scan)

        # Check scan settings
        self.assertEqual(scan.scan_type, config[SCAN_TYPE])
        self.assertEqual(scan.steps, config[STEPS])
        self.assertEqual(scan.actual_step, config[ACTUAL_STEP])
        self.assertEqual(scan.start_positions, config[START_POSITIONS])
        self.assertEqual(scan.stop_positions, config[STOP_POSITIONS])

    def _assert_full_scan(self, config):
        scan = self._scan
        shape = np.add(config[STEPS], 1)
        total_steps = np.prod(shape)
        default_value = np.arange(total_steps)

        # Check scan settings
        self.assertEqual(scan.actual_step, total_steps - 1)

        # Check devices
        self.assertEqual(len(scan.motors), len(config[MOTORS]))
        for index, motor in enumerate(scan._motors):
            data = (default_value + index).reshape(shape)
            np.testing.assert_array_equal(motor.data, data)

        self.assertEqual(len(scan.data_sources), len(config[SOURCES]))
        for index, source in enumerate(scan._data_sources):
            data = ((default_value + index) ** 2).reshape(shape)
            np.testing.assert_array_equal(source.data, data)

        # Check plots
        if config[SCAN_TYPE] in MESHES:
            self._assert_heatmap(config)
        else:
            self._assert_multicurve_plot(config)

    def _assert_multicurve_plot(self, config):
        # Check if plot follows with the number of motors
        controller = self.controller._controller._current_plot
        self.assertTrue(isinstance(controller, MultiCurvePlot))

        # Check number of curves, this is equal to:
        # num_motors + num_sources - 1 (since one data is x_data)
        plot_items = controller._items._items
        self.assertEqual(len(plot_items), len(config[SOURCES]))

        # Check if values are set in the PlotDataItem
        total_steps = config[STEPS][0] + 1
        for item, plot_config in plot_items.items():
            x_data = plot_config[X_DATA].data
            y_data = plot_config[Y_DATA].data

            self.assertEqual(len(x_data), total_steps)
            self.assertEqual(len(y_data), total_steps)

            np.testing.assert_array_equal(item.xData, x_data)
            np.testing.assert_array_equal(item.yData, y_data)

    def _assert_heatmap(self, config):
        controller = self.controller._controller._current_plot
        self.assertTrue(isinstance(controller, HeatmapPlot))

        # Check image dimensions
        height, width = np.add(config[STEPS], 1)
        self.assertEqual(controller.height, height)
        self.assertEqual(controller.width, width)

        # Check consistency of data and image item
        z_data = np.array(controller.config[Z_DATA].data)

        # Manage reversed properties
        diff = np.subtract(config[STOP_POSITIONS], config[START_POSITIONS])
        is_reversed = [d == 1 for d in np.sign(diff)]
        if is_reversed[0]:
            z_data = np.fliplr(z_data)
        if is_reversed[1]:
            z_data = np.flipud(z_data)

        self.assertEqual(z_data.shape, (height, width))
        image = controller.widget.plot().image
        np.testing.assert_array_equal(image.data, z_data)
