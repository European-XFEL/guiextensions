import numpy as np
from traits.api import (
    Array, HasStrictTraits, Instance, Int, List, ListStr, Property, Str,
    cached_property)

from ..const import MESHES
from .device import DataSource, Device, Motor


class Scan(HasStrictTraits):
    """This contains the scan config from Karabacon. This also hosts the
       motor and source devices, which is created based on the scan type and
       the number of data sources, respectively."""

    scan_type = Str
    actual_step = Int
    steps = Property(Array)
    current_index = Array

    devices = Property(List(Instance(Device)),
                       depends_on=["_motors", "_data_sources"])
    motors = Property(ListStr, depends_on="_motors")
    data_sources = Property(ListStr, depends_on="_data_sources")

    motor_ids = Property(List(Str))
    data_source_ids = Property(List(Str))
    start_positions = Property(Array)
    stop_positions = Property(Array)

    _motors = List(Instance(Motor))
    _data_sources = List(Instance(DataSource))

    @cached_property
    def _get_steps(self):
        steps = np.array([motor.step for motor in self._motors])
        if self.scan_type not in MESHES:
            # Get only an array of one element (since all are identical)
            steps = steps[:1]
        return steps

    def _set_steps(self, steps):
        shape = steps + 1 if self.scan_type in MESHES else None
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

    def _set_motors(self, names):
        self._motors = [Motor(name=name) for name in names]

    @cached_property
    def _get_data_sources(self):
        return [source.name for source in self._data_sources]

    def _set_data_sources(self, names):
        self._data_sources = [DataSource(name=name) for name in names]

    @cached_property
    def _get_motor_ids(self):
        return [motor.device_id for motor in self._motors]

    def _set_motor_ids(self, motor_ids):
        for motor_id, motor in zip(motor_ids, self._motors):
            motor.device_id = motor_id

    @cached_property
    def _get_data_source_ids(self):
        return [source.device_id for source in self._data_sources]

    def _set_data_source_ids(self, data_source_ids):
        for source_id, source in zip(data_source_ids, self._data_sources):
            source.device_id = source_id

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
        if name in self.motor_ids:
            return self._motors[self.motor_ids.index(name)]

        if name in self.data_source_ids:
            return self._data_sources[self.data_source_ids.index(name)]
