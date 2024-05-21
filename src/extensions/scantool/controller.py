from qtpy.QtWidgets import QGraphicsScene, QGridLayout, QWidget
from traits.api import (
    Dict, Event, HasStrictTraits, Instance, List, on_trait_change)

from .const import (
    ACTUAL_STEP, ADD, ALIGNER, CURRENT_INDEX, MESHES, MOTOR_IDS, MOTORS,
    REMOVE_ALL, SCAN_TYPE, SOURCE_IDS, SOURCES, START_POSITIONS, STEPS,
    STOP_POSITIONS, X_DATA, Y_DATA, Z_DATA)
from .data.scan import Scan
from .plots.base import BasePlot
from .plots.heatmap import HeatmapPlot
from .plots.multicurve import MultiCurvePlot
from .selection.controller import DataSelectionController
from .widgets import get_container


class ScanController(HasStrictTraits):

    widget = Instance(QWidget)
    scans = List(Instance(Scan))

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
        self.use_multicurve_plot()
    # ---------------------------------------------------------------------
    # Public methods

    def new_scan(self, config, realtime=True):
        """Initializes a new scan object which stores the scan parameters and
           device objects

        Args:
            config (dict): scan configuration
            realtime (bool, optional): Indicates if the scan is a realtime. If
            True, then previous plots are cleared. Defaults to True.

        Returns:
            Scan: scan object
        """

        # Do not add scan that is already displayed in the plot
        if not realtime and self.scans:
            source_ids = [scan.data_source_ids for scan in self.scans]
            if config[SOURCE_IDS] in source_ids:
                return

        scan = Scan(scan_type=config[SCAN_TYPE],
                    motors=config[MOTORS],
                    data_sources=config[SOURCES],
                    motor_ids=config[MOTOR_IDS],
                    data_source_ids=config[SOURCE_IDS],
                    actual_step=config[ACTUAL_STEP],
                    steps=config[STEPS],
                    current_index=config[CURRENT_INDEX],
                    start_positions=config[START_POSITIONS],
                    stop_positions=config[STOP_POSITIONS])

        clear_all = True
        # Do not plot multiple plots and clear existing plots if:
        # - new scan is a realtime scan or a mesh.
        # - previous scan was mesh.
        # - motor aliases do not match.
        # We do not have to inspect all scan members because we are
        # interested if the last plot was a mesh.
        # On a new mesh all previous plots are cleaned.

        if (self.scans and not realtime and scan.scan_type not in MESHES
                and self.scans[-1].scan_type not in MESHES
                and scan.motor_ids == self.scans[-1].motor_ids):
            clear_all = False

        if self.scans and clear_all:
            self.scans.clear()
            self._data_selection.clear()

        self.scans.append(scan)

        return scan

    def update(self, device):
        """Updates the current plot with every device value update. The plot
           would have the responsibility to check if the device is linked
           (or its data are viewed)."""
        self._current_plot.update(device)

    def use_multicurve_plot(self):
        """Uses the multicurve plot controller for 1D data.
           By default, all devices are used.
           Motor 1 (pos0) is x_data, others are y_data"""
        if self.scans:
            x_data = self.scans[0].motor_ids[0]
            source_ids = []
            for scan in self.scans:
                source_ids.extend(scan.data_source_ids)
            self._config[MultiCurvePlot] = [
                {X_DATA: x_data, Y_DATA: y_data} for y_data in source_ids]

        append_scan = len(self.scans) > 1
        return self._use_plot(MultiCurvePlot, append_scan)

    def use_heatmap_plot(self):
        """Uses the heatmap for 2D data.
           `steps` are used for image dimensions.
           By default, only three devices are used.
           Motor 1 and 2 (pos0 and pos 1) are x_data and y_data, respectively,
           Data source 1 (y0) is z_data."""
        config = self._config[HeatmapPlot]
        scan = self.scans[-1]

        # Check if previously selected devices are present in the new scan.
        # Remove from the config if not.
        for conf in config[:]:
            if (conf[X_DATA] not in scan.motor_ids
                    or conf[Y_DATA] not in scan.motor_ids
                    or conf[Z_DATA] not in scan.data_source_ids):
                config.remove(conf)

        # Prepare a default config
        if not config:
            self._config[HeatmapPlot] = [{
                X_DATA: scan.motor_ids[1],
                Y_DATA: scan.motor_ids[0],
                Z_DATA: scan.data_source_ids[0]}]

        return self._use_plot(HeatmapPlot)

    def update_vector_data(self, data):
        self._current_plot.update_vector_data(data)

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

    def enable_data_selection(self, state):
        self._data_selection.widget.setEnabled(state)

    def enable_clear_button(self, state):
        self._data_selection.set_clear_button_enabled(state)

    def update_aligner_results(self, data):
        if self._current_plot is None:
            return
        self._current_plot.remove_aligner_results()
        if data is None:
            return

        for item in data:
            # Add valid positions
            if not item["moveToPositions"]:
                continue
            if self.scans[-1].scan_type in MESHES:
                source_id = item["sourceId"]
                self._current_plot.add_aligner_result(
                    motor=self.scans[-1].motor_ids[0],
                    source=source_id,
                    positions=item["motorPositions"],
                    label=item["name"])
            else:
                for index, motor_pos in enumerate(item["motorPositions"]):
                    motor_id = self.scans[-1].motor_ids[index]
                    source_id = item["sourceId"]
                    self._current_plot.add_aligner_result(
                        motor=motor_id,
                        source=source_id,
                        positions=[motor_pos],
                        label=item["name"])
        self._current_plot.hide_aligner_results()
        if self._data_selection.aligner_results_enabled():
            self._current_plot.show_aligner_result(
                motor_id=self.scans[-1].motor_ids[0],
                source_id=self.scans[-1].data_source_ids[0])

    # ---------------------------------------------------------------------
    # Private methods

    def _mouse_double_clicked(self, event):
        plot_item = self._current_plot.widget.plotItem
        scene_coords = event.scenePos()

        QGraphicsScene.mouseDoubleClickEvent(plot_item.scene(), event)
        if plot_item.vb.sceneBoundingRect().contains(scene_coords):
            pos = plot_item.vb.mapSceneToView(scene_coords)
            self._plot_double_clicked = {
                "coord": [pos.x(), pos.y()],
                "aliases": self._data_selection.get_selected_motors()}

    def _use_plot(self, klass, append_scan=False):
        """Generic class to remove and destroy existing plot and
           instantiate the requested plot class and add its widget to the
           base widget layout."""

        # 1. Switch to selected plot
        if not append_scan:
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
        if append_scan:
            config = config[-len(self.scans[-1].data_source_ids):]

        for conf in config:
            self._current_plot.add(self._map_to_devices(conf),
                                   update=False)

        # 2. Set axes labels based on plot config
        self._set_axes_labels(self._config[klass])

        # 3. Finalize plot setup by informing listeners
        self._plot_refreshed = klass

        # 4. Reimplement mouseDoubleCkickedEvent
        # We can not use sigMouseClicked signal of plotItem due to the bug in
        # pyqtgraph: double click is not detected.
        self._current_plot.widget.plotItem.scene().mouseDoubleClickEvent =\
            self._mouse_double_clicked

        return self._current_plot

    def _map_to_devices(self, config):
        # Map the string to the device.
        # `config` is in the form of {ADD: [(item, config), (item, config)]}
        for scan in self.scans:
            scan_map = {axis: scan.get_device(device_name)
                        for axis, device_name in config.items()}
            if None not in scan_map.values():
                return scan_map

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
            if self.scans:
                motor_ids = []
                source_ids = []
                for scan in self.scans:
                    motor_ids.extend(scan.motor_ids)
                    source_ids.extend(scan.data_source_ids)
                self._data_selection.set_devices(
                    motor_ids=motor_ids,
                    source_ids=source_ids)
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
        if self._current_plot is None or not self.scans:
            return
        config = self._config[type(self._current_plot)]

        self._current_plot.clear()
        self._current_plot.hide_aligner_results()

        if REMOVE_ALL in changes:
            self._set_axes_labels(config=None, changes=None)
            self.scans.clear()
            self._current_plot.clear_pen_map()
            self._current_plot = None
            return

        if ADD in changes:
            for added in changes[ADD]:
                config.append(added)
                self._current_plot.add(self._map_to_devices(added))
                if changes.get(ALIGNER):
                    if self.scans[-1].scan_type in MESHES:
                        self._current_plot.show_aligner_result(
                            motor_id=None, source_id=added[Z_DATA])
                    else:
                        self._current_plot.show_aligner_result(
                            motor_id=added[X_DATA], source_id=added[Y_DATA])
            self._set_axes_labels(config, changes)

    def _set_axes_labels(self, config, changes=None):
        if config:
            current_config = changes[ADD] if changes else config
            x_label = current_config[0][X_DATA]
            sources = [c[Y_DATA] for c in current_config]
            y_label = "" if len(sources) > 1 else sources[0]
            for idx, label in enumerate([x_label, y_label]):
                self._current_plot.widget.set_label(idx, label)
        else:
            for axis in [0, 1]:
                self._current_plot.widget.set_label(axis, "")
