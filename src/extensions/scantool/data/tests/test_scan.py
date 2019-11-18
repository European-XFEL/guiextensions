from unittest import TestCase

import numpy as np

from ..scan import Scan
from ...const import (
    ACTUAL_STEP, CURRENT_INDEX, NUM_DATA_SOURCES, SCAN_TYPE, START_POSITIONS,
    STEPS, STOP_POSITIONS)
from ...tests.confs import ASCAN_CONFIG, A2SCAN_CONFIG, MESH_CONFIG
from ...utils import get_num_motors


class TestScan(TestCase):

    def test_basics(self):
        self._assert_scan_config(ASCAN_CONFIG)
        self._assert_scan_config(A2SCAN_CONFIG)
        self._assert_scan_config(MESH_CONFIG)

    def _assert_scan_config(self, config):
        scan = Scan(scan_type=config[SCAN_TYPE],
                    num_sources=config[NUM_DATA_SOURCES],
                    actual_step=config[ACTUAL_STEP],
                    steps=config[STEPS],
                    current_index=config[CURRENT_INDEX],
                    start_positions=config[START_POSITIONS],
                    stop_positions=config[STOP_POSITIONS])

        # Check scan settings
        self.assertEqual(scan.scan_type, config[SCAN_TYPE])
        self.assertEqual(scan.num_sources, config[NUM_DATA_SOURCES])
        self.assertEqual(scan.actual_step, config[ACTUAL_STEP])
        np.testing.assert_array_equal(scan.steps, config[STEPS])
        np.testing.assert_array_equal(scan.current_index,
                                      config[CURRENT_INDEX])
        np.testing.assert_array_equal(scan.start_positions,
                                      config[START_POSITIONS])
        np.testing.assert_array_equal(scan.stop_positions,
                                      config[STOP_POSITIONS])

        # Check devices
        self.assertEqual(len(scan.motors), get_num_motors(config[SCAN_TYPE]))
        expected_shape = np.add(config[STEPS], 1)
        for motor in scan._motors:
            np.testing.assert_array_equal(motor.data.shape, expected_shape)

        self.assertEqual(len(scan.data_sources), config[NUM_DATA_SOURCES])
        for source in scan._data_sources:
            np.testing.assert_array_equal(source.data.shape, expected_shape)
