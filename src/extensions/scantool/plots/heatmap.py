#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import numpy as np
from pyqtgraph import ArrowItem, TextItem
from traits.api import (
    ArrayOrNone, Bool, Dict, Int, List, ListBool, on_trait_change)

from ..const import MOTOR_NAMES, X_DATA, Y_DATA, Z_DATA
from .base import ImagePlot


class HeatmapPlot(ImagePlot):

    config = Dict({X_DATA: None, Y_DATA: None, Z_DATA: None})

    width = Int(50)
    height = Int(50)

    _reversed = ListBool
    _offset = ArrayOrNone
    _transposed = Bool(False)
    _labels = List()

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

    def add_aligner_result(self, motor, source, positions, label):
        # To avoid overlaping textItem and arrows check if there is a textItem
        # with the same devices and coordinates.
        # If yes we update the existing label and do not add a new TextItem
        for item in self._aligner_results:
            if (item["motor"] != motor or item["source"] != source or
               not isinstance(item["plot_item"], TextItem)):
                continue
            if (item["plot_item"].pos().x() == positions[0]
               and item["plot_item"].pos().y() == positions[1]):
                label = f"{label}, {item['plot_item'].toPlainText()}"
                item["plot_item"].setText(label)
                return

        label = f"{label} ({source})"
        text_item = TextItem(html=label, anchor=(-0.3, -0.3), angle=0,
                             border="w", fill=(255, 255, 255))
        text_item.setPos(positions[0], positions[1])
        self.widget.plotItem.addItem(text_item)

        arrow_item = ArrowItem(pos=(positions[0], positions[1]), angle=-45)
        self.widget.plotItem.addItem(arrow_item)
        for plot_item in [text_item, arrow_item]:
            self._aligner_results.append({"motor": motor, "source": source,
                                          "plot_item": plot_item})

    def update(self, device):
        """For now, this heatmap only considers updates from the z_data.
           This is because it assumes that updates are continuous and
           unidirectional. x_data and y_data are already considered on the
           image item setup."""
        if device is not self.config[Z_DATA]:
            return

        if device.current_index is None:
            self.clear()
            return

        # Get image properties
        current_row = device.current_index[0] + 1
        z_data = np.copy(device.data[:current_row])
        min_data = np.nanmin(z_data)

        # Check if there are nans (may be due to gaps)
        # Replace with min data if any to not interfere with colormap.
        finite = np.isfinite(z_data)
        if not np.all(finite):
            z_data[~finite] = min_data

        # Now, prepare the plot item
        plotItem = self.widget.plot()

        # Transpose data if x- and y-axis are interchanged/inverted
        if self._transposed:
            z_data = z_data.T.copy()

        # Manage reversed properties
        if self._reversed[0]:
            z_data = np.fliplr(z_data)
        if self._reversed[1]:
            z_data = np.flipud(z_data)

        # Set data
        plotItem.setData(z_data, update=False)

        # Apply offset to only show images at their respective values since
        # our images do not have opacity
        if self._reversed[0] and self._transposed:
            width = z_data.shape[1]
            plotItem.set_translation(x_translate=self._offset[width - 1],
                                     update=False)

        elif self._reversed[1] and not self._transposed:
            height = z_data.shape[0]
            plotItem.set_translation(y_translate=self._offset[height - 1],
                                     update=False)

    def update_vector_data(self, data):
        # Get image properties
        z_data = data
        min_data = np.nanmin(z_data)

        # Check if there are nans (may be due to gaps)
        z_data[np.isnan(z_data)] = min_data

        # Now, prepare the plot item
        plotItem = self.widget.plot()

        # Transpose data if x- and y-axis are interchanged/inverted
        if self._transposed:
            z_data = z_data.T.copy()

        # Manage reversed properties
        if self._reversed[0]:
            z_data = np.fliplr(z_data)
        if self._reversed[1]:
            z_data = np.flipud(z_data)

        # Set data
        plotItem.setData(z_data, update=True)

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
        if x_start > x_stop:
            x_start, x_stop = x_stop, x_start
            is_reversed[0] = True
        if y_start > y_stop:
            y_start, y_stop = y_stop, y_start
            is_reversed[1] = True
        self._reversed = is_reversed

        # Compute scale and translation
        y_scale = abs(y_stop - y_start) / y_device.step
        x_scale = abs(x_stop - x_start) / x_device.step

        # Calculate offset to center pixels to axis tick values
        x_offset = x_scale / 2
        y_offset = y_scale / 2

        # Ugly check if axes is inverted
        self._transposed = x_device.name != MOTOR_NAMES[1]

        # Compute offset for rolling images
        if self._transposed:
            self._offset = np.linspace(x_stop, x_start, self.width) - x_offset
        else:
            self._offset = np.linspace(y_stop, y_start, self.height) - y_offset

        plotItem = self.widget.plot()
        plotItem.set_transform(x_scale=x_scale,
                               y_scale=y_scale,
                               x_translate=x_start - x_offset,
                               y_translate=y_start - y_offset)

        plotItem.vb.setRange(xRange=(x_start, x_stop),
                             yRange=(y_start, y_stop))
