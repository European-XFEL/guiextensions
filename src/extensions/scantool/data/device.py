import numpy as np
from traits.api import (
    Array, ArrayOrNone, cached_property, Float, HasStrictTraits, Int,
    Property, Str)

DEFAULT_SHAPE = 10


class Device(HasStrictTraits):
    name = Str
    data = Property(Array, depends_on="current_index")
    current_index = ArrayOrNone

    _data = Array
    _shape = ArrayOrNone

    def add(self, data, current_index):
        # No data shape means self._data is just a container of the actual
        # data. This means that the container is sometimes smaller than the
        # current index. There is a need to adjust the container length before
        # storing the data.
        # This is the case for cnscans, thus below is assumed for 1D array.
        if self._shape is None:
            # Use internal current index. cscan current index is unusable.
            if self.current_index is not None:
                current_index = self.current_index + 1
            else:
                current_index = np.array([0])

            # Adjust container length if the new size exceeds the current one.
            size = current_index[0]
            if size > self._data.size:
                new_data = np.full(size * 2, np.nan)
                new_data[:size] = self.data
                self._data = new_data

        self.current_index = current_index
        self._data[tuple(current_index)] = data

    def new_data(self, shape=None):
        self._shape = shape
        # Use a default shape if not specified, usually for continuous scan
        if shape is None:
            shape = DEFAULT_SHAPE
        self._data = np.full(shape, np.nan)

    @cached_property
    def _get_data(self):
        # If data shape is known, self._data is the actual data.
        # This is the usual case (anscans, dnscans, meshes).
        if self._shape is not None:
            return self._data

        # No data shape means self._data is just a container of the actual
        # data. This means, we need to slice in order to get that subset.
        # This is the case for cnscans, thus below is assumed for 1D array.
        if self.current_index is None:
            return np.array([])

        length = self.current_index[0] + 1
        return self._data[:length]


class Motor(Device):
    start_position = Float
    stop_position = Float
    step = Int


class DataSource(Device):
    """Placeholder for data source devices"""