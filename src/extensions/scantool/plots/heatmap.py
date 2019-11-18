#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import numpy as np
from traits.api import ArrayOrNone, Dict, Int, List, ListBool, on_trait_change

from .base import ImagePlot
from ..const import X_DATA, Y_DATA, Z_DATA


class HeatmapPlot(ImagePlot):

    config = Dict({X_DATA: None, Y_DATA: None, Z_DATA: None})

    width = Int(50)
    height = Int(50)

    _x_range = List
    _y_range = List
    _reversed = ListBool
    _y_positions = ArrayOrNone

    def __init__(self, parent=None):
        super(HeatmapPlot, self).__init__(parent)

        # Setup plot widget
        plotItem = self.widget.plot()
        plotItem.vb.disableAutoRange()
        plotItem.set_aspect_ratio(0)

    def add(self, config, update=True):
        self.config.update(config)
        if update:
            self.update(config[Z_DATA])

    def update(self, device):
        """For now, this heatmap only considers updates from the z_data.
           This is because it assumes that updates are continuous and
           unidirectional. x_data and y_data are already considered on the
           image item setup."""
        if device is not self.config[Z_DATA]:
            return

        if len(device.data) == 0:
            self.clear()
            return

        # Get image properties
        current_row = device.current_index[0] + 1
        y_data = np.copy(device.data[:current_row])
        min_data = np.nanmin(y_data)

        # Check if there are nans (may be due to gaps)
        # Replace with min data if any to not interfere with colormap.
        finite = np.isfinite(y_data)
        if not np.all(finite):
            y_data[~finite] = min_data

        # Now, prepare the plot item
        plotItem = self.widget.plot()

        # Manage reversed properties
        if self._reversed[0]:
            y_data = np.fliplr(y_data)

        # Reversed motor start/stop positions on y-axis is more critical as we
        # need to change the offset as the height grows
        if self._reversed[1]:
            y_data = np.flipud(y_data)

            height = y_data.shape[0]
            plotItem.set_translation(y_translate=self._y_positions[height - 1],
                                     update=False)

        plotItem.setData(y_data, update=False)

    def clear(self):
        """Clear the image plot by setting empty image"""
        empty_image = np.zeros((self.height, self.width))
        self.widget.plot().setData(empty_image, update=False)

    @on_trait_change("config_items", post_init=True)
    def _set_dimensions(self, event):
        x_device = self.config[X_DATA]
        y_device = self.config[Y_DATA]

        # Check if the devices for the image dimensions are changed
        old_devices = (event.changed[X_DATA], event.changed[Y_DATA])
        if old_devices == (x_device, y_device):
            return

        self.height = y_device.step + 1
        self.width = x_device.step + 1
        self.clear()

        # Calculate absolute start and stop positions
        y_start, x_start = y_device.start_position, x_device.start_position
        y_stop, x_stop = y_device.stop_position, x_device.stop_position
        is_reversed = [False, False]
        y_positions = None

        if x_start > x_stop:
            x_start, x_stop = x_stop, x_start
            is_reversed[0] = True

        if y_start > y_stop:
            y_start, y_stop = y_stop, y_start
            is_reversed[1] = True
            y_positions = np.linspace(y_stop, y_start, self.height)

        self._x_range = [x_start, x_stop]
        self._y_range = [y_start, y_stop]
        self._reversed = is_reversed
        self._y_positions = y_positions

        # Compute scale
        y_scale = (y_stop - y_start) / y_device.step
        x_scale = (x_stop - x_start) / x_device.step

        plotItem = self.widget.plot()
        plotItem.set_transform(x_scale=x_scale,
                               y_scale=y_scale,
                               x_translate=x_start,
                               y_translate=y_start)

        plotItem.vb.setRange(xRange=(x_start, x_stop),
                             yRange=(y_start, y_stop))
