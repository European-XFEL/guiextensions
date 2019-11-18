import numpy as np
from traits.api import (
    Array, cached_property, HasStrictTraits, Instance, Int, List, ListStr,
    Property, Str)

from .device import DataSource, Device, Motor
from ..const import CSCANS, MESHES, MOTOR_NAMES, SOURCE_NAMES
from ..utils import get_num_motors


class Scan(HasStrictTraits):
    """This contains the scan config from Karabacon. This also hosts the
       motor and source devices, which is created based on the scan type and
       the number of data sources, respectively."""

    scan_type = Str
    num_sources = Int
    actual_step = Int
    steps = Property(Array)
    current_index = Array

    devices = Property(List(Instance(Device)),
                       depends_on=["_motors", "_data_sources"])
    motors = Property(ListStr, depends_on="_motors")
    data_sources = Property(List(Instance(DataSource)),
                            depends_on="_data_sources")

    start_positions = Property(Array)
    stop_positions = Property(Array)

    _motors = List(Instance(Motor))
    _data_sources = List(Instance(DataSource))

    def _scan_type_changed(self, scan_type):
        self._motors = [Motor(name=name)
                        for name in MOTOR_NAMES[:get_num_motors(scan_type)]]

    def _num_sources_changed(self, num_sources):
        self._data_sources = [DataSource(name=name)
                              for name in SOURCE_NAMES[:num_sources]]

    @cached_property
    def _get_steps(self):
        steps = np.array([motor.step for motor in self._motors])
        if self.scan_type not in MESHES:
            # Get only an array of one element (since all are identical)
            steps = steps[:1]
        return steps

    def _set_steps(self, steps):
        shape = None if self.scan_type in CSCANS else steps + 1
        for device in self.devices:
            device.new_data(shape)

        # Check if number of steps is equal to the number of motors (which
        # usually happens with meshes). If not, check if steps is in 1D
        # (which is the case for xnscans).
        if self.scan_type not in MESHES:
            steps = steps.tolist() * len(self._motors)

        for motor, step in zip(self._motors, steps):
            motor.step = step

    @cached_property
    def _get_devices(self):
        return self._motors + self._data_sources

    @cached_property
    def _get_motors(self):
        return [motor.name for motor in self._motors]

    @cached_property
    def _get_data_sources(self):
        return [source.name for source in self._data_sources]

    @cached_property
    def _get_start_positions(self):
        return [motor.start_position for motor in self._motors]

    def _set_start_positions(self, positions):
        for pos, motor in zip(positions, self._motors):
            motor.start_position = pos

    @cached_property
    def _get_stop_positions(self):
        return [motor.stop_position for motor in self._motors]

    def _set_stop_positions(self, positions):
        for pos, motor in zip(positions, self._motors):
            motor.stop_position = pos

    def get_device(self, name):
        if name in self.motors:
            return self._motors[self.motors.index(name)]

        if name in self.data_sources:
            return self._data_sources[self.data_sources.index(name)]
