from qtpy.QtWidgets import QGraphicsScene, QGridLayout, QWidget
from traits.api import Dict, Event, HasStrictTraits, Instance, on_trait_change

from .const import (
    A4SCAN_CONFIG, ACTUAL_STEP, ADD, CURRENT_INDEX, MOTOR_IDS, MOTORS, REMOVE,
    SCAN_TYPE, SOURCE_IDS, SOURCES, START_POSITIONS, STEPS, STOP_POSITIONS,
    X_DATA, Y_DATA, Z_DATA)
from .data.scan import Scan
from .plots.base import BasePlot
from .plots.heatmap import HeatmapPlot
from .plots.multicurve import MultiCurvePlot
from .selection.controller import DataSelectionController
from .widget import get_container


class ScanController(HasStrictTraits):

    widget = Instance(QWidget)
    scan = Instance(Scan)

    _current_plot = Instance(BasePlot)
    _data_selection = Instance(DataSelectionController)
    _config = Dict({
        MultiCurvePlot: [],
        HeatmapPlot: []
    })

    _plot_refreshed = Event
    _plot_double_clicked = Event

    def __init__(self, parent=None):
        super(ScanController, self).__init__()
        self.widget = get_container(parent, QGridLayout())
        # Add default scan for initial plot visualization
        self.new_scan(A4SCAN_CONFIG)
        self.use_multicurve_plot()

    # ---------------------------------------------------------------------
    # Public methods

    def new_scan(self, config):
        """Initializes a new scan object which stores the scan parameters and
           device objects"""
        self.scan = Scan(scan_type=config[SCAN_TYPE],
                         motors=config[MOTORS],
                         data_sources=config[SOURCES],
                         motor_ids=config[MOTOR_IDS],
                         data_source_ids=config[SOURCE_IDS],
                         actual_step=config[ACTUAL_STEP],
                         steps=config[STEPS],
                         current_index=config[CURRENT_INDEX],
                         start_positions=config[START_POSITIONS],
                         stop_positions=config[STOP_POSITIONS])

        return self.scan

    def update(self, device):
        """Updates the current plot with every device value update. The plot
           would have the responsibility to check if the device is linked
           (or its data are viewed)."""
        self._current_plot.update(device)

    def use_multicurve_plot(self):
        """Uses the multicurve plot controller for 1D data.
           By default, all devices are used.
           Motor 1 (pos0) is x_data, others are y_data"""

        config = self._config[MultiCurvePlot]

        # Check if previously selected devices are present in the new scan.
        # Remove from the config if not.
        for conf in config[:]:
            if (conf[X_DATA] not in self.scan.motor_ids
                    or conf[Y_DATA] not in self.scan.data_source_ids):
                config.remove(conf)

        if not config:
            # Set up default plot config by using pos0 as x_data
            # and others as y_data
            x_data = self.scan.motor_ids[0]
            source_ids = self.scan.data_source_ids

            # Populate the plot by specifying x_data and y_data
            self._config[MultiCurvePlot] = [
                {X_DATA: x_data, Y_DATA: y_data} for y_data in source_ids]

        return self._use_plot(MultiCurvePlot)

    def use_heatmap_plot(self):
        """Uses the heatmap for 2D data.
           `steps` are used for image dimensions.
           By default, only three devices are used.
           Motor 1 and 2 (pos0 and pos 1) are x_data and y_data, respectively,
           Data source 1 (y0) is z_data."""
        config = self._config[HeatmapPlot]

        # Check if previously selected devices are present in the new scan.
        # Remove from the config if not.
        for conf in config[:]:
            if (conf[X_DATA] not in self.scan.motor_ids
                    or conf[Y_DATA] not in self.scan.motor_ids
                    or conf[Z_DATA] not in self.scan.data_source_ids):
                config.remove(conf)

        # Prepare a default config
        if not config:
            self._config[HeatmapPlot] = [{
                X_DATA: self.scan.motor_ids[1],
                Y_DATA: self.scan.motor_ids[0],
                Z_DATA: self.scan.data_source_ids[0]}]

        return self._use_plot(HeatmapPlot)

    def add_data_selection(self):
        """Adds a controller of a selection widget, which can be used to
        toggle the data to be viewed and at which axis."""
        if self._data_selection is None:
            self._data_selection = DataSelectionController(parent=self.widget)
            self._data_selection.on_trait_event(self._change_plot_items,
                                                "changed")

            self.widget.add_widget(self._data_selection.widget, row=0, col=1)

            # Add initial selection widget based on default scan config
            self._on_plot_refresh(type(self._current_plot))

        return self._data_selection

    # ---------------------------------------------------------------------
    # Private methods

    def _mouse_double_clicked(self, event):
        QGraphicsScene.mouseDoubleClickEvent(
            self._current_plot.widget.plotItem.scene(), event)
        scene_coords = event.scenePos()
        plot_item = self._current_plot.widget.plotItem
        if plot_item.sceneBoundingRect().contains(scene_coords):
            pos = plot_item.vb.mapSceneToView(scene_coords)
            self._plot_double_clicked = {
                "coord": [pos.x(), pos.y()],
                "aliases": self._data_selection.get_selected_motors()}

    def _use_plot(self, klass):
        """Generic class to remove and destroy existing plot and
           instantiate the requested plot class and add its widget to the
           base widget layout."""

        # 1. Switch to selected plot
        if not isinstance(self._current_plot, klass):
            if self._current_plot is not None:
                # Remove this unwanted plot
                self.widget.remove_widget(self._current_plot.widget)
                self._current_plot.destroy()
            self._current_plot = klass(parent=self.widget)
            self.widget.add_widget(self._current_plot.widget, row=0, col=0)
        else:
            # Reset!
            self._current_plot.clear()

        config = self._config[klass]
        for conf in config:
            self._current_plot.add(self._map_to_devices(conf),
                                   update=False)

        # 2. Set axes labels based on plot config
        self._set_axes_labels(config)

        # 3, Finalize plot setup by informing listeners
        self._plot_refreshed = klass

        # 4. Reimplement mouseDoubleCkickedEvent
        # We can not use sigMouseClicked signal of scene due to the bug in
        # pyqtgraph: double click is not detected.
        self._current_plot.widget.plotItem.scene().mouseDoubleClickEvent =\
            self._mouse_double_clicked

        return self._current_plot

    def _map_to_devices(self, config):
        # Map the string to the device.
        # `config` is in the form of {ADD: [(item, config), (item, config)]}
        return {axis: self.scan.get_device(device_name)
                for axis, device_name in config.items()}

    def _map_to_names(self, config):
        return {axis: device.device_id for axis, device in config.items()}

    # ---------------------------------------------------------------------
    # trait handlers

    @on_trait_change("_plot_refreshed")
    def _on_plot_refresh(self, plot_type):
        if self._data_selection is not None:
            if plot_type is HeatmapPlot:
                self._data_selection.use_image_selection()
            elif plot_type is MultiCurvePlot:
                self._data_selection.use_xy_selection()
            else:
                raise NotImplementedError("Plot type not implemented yet.")

            # Check if devices are changed completely
            self._data_selection.set_devices(
                motors=self.scan.motors,
                sources=self.scan.data_sources,
                motor_ids=self.scan.motor_ids,
                source_ids=self.scan.data_source_ids)
            self._data_selection.set_config(self._config[plot_type])

    @on_trait_change("scan:current_index")
    def _current_index_changed(self, index):
        self._current_plot.current_index = index

    def _change_plot_items(self, changes):
        """Changes the viewed data by passing the change request, which is
           in the form of:
              `changes = {ADD: [(item, config), (item, config)],
                          REMOVE: [(item, config), (item, config)]}`
           The config is a dict of:
              plot-specific keys (e.g. X_DATA)
              device name values (e.g. 'pos0')
           The config values need to be mapped to the respective device object.
        """
        if self._current_plot is None:
            return
        config = self._config[type(self._current_plot)]

        if REMOVE in changes:
            for removed in changes[REMOVE]:
                if removed in config:
                    config.remove(removed)
                self._current_plot.remove(self._map_to_devices(removed))

        if ADD in changes:
            for added in changes[ADD]:
                config.append(added)
                self._current_plot.add(self._map_to_devices(added))

            self._set_axes_labels(config)

    def _set_axes_labels(self, config):
        # Change labels if necessary
        for axis, data in enumerate([X_DATA, Y_DATA]):
            name = set([device[data] for device in config])
            if len(name) == 1:
                self._current_plot.widget.set_label(axis, next(iter(name)))
