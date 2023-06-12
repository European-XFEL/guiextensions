#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtWidgets import QMessageBox
from traits.api import Bool, Instance, on_trait_change

from karabo.common.api import WeakMethodRef
from karabo.common.states import State
from karabogui.api import call_device_slot, get_reason_parts, messagebox
from karabogui.binding.api import (
    PropertyProxy, VectorHashBinding, WidgetNodeBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)

from .models.api import ScantoolBaseModel
from .scantool.const import (
    ACTUAL_STEP, ALIGNER, CURRENT_INDEX, IS_SPECTRUM_DATA, MESHES, MOTOR_IDS,
    MOTOR_NAMES, MOTORS, SCAN_TYPE, SOURCE_IDS, SOURCE_NAMES, SOURCES,
    SPECTRUM_DATA, START_POSITIONS, STEPS, STOP_POSITIONS)
from .scantool.controller import ScanController
from .scantool.data.scan import Scan

HISTORY_PROXY_PATH = "history.output.schema.data"


@register_binding_controller(
    ui_name='Scantool Base Widget',
    klassname='Scantool-Base',
    binding_type=(WidgetNodeBinding, VectorHashBinding),
    is_compatible=with_display_type('WidgetNode|Scantool-Base'),
    priority=0, can_show_nothing=False)
class ScantoolDynamicWidget(BaseBindingController):
    model = Instance(ScantoolBaseModel, args=())

    _controller = Instance(ScanController)
    # Scan contains the scan parameters, device objects
    _scan = Instance(Scan)
    _history_proxy = Instance(PropertyProxy)

    _is_scanning = Bool(False)
    _first_proxy_received = Bool(False)
    _plot_available = Bool(False)

    def create_widget(self, parent):
        self._controller = ScanController(parent=parent)
        self._controller.add_data_selection()
        return self._controller.widget

    def add_proxy(self, proxy):
        if proxy.path == HISTORY_PROXY_PATH and self._history_proxy is None:
            self._history_proxy = proxy
            return True
        else:
            return False

    def value_update(self, proxy):
        # This is for initialization.
        # binding_update only gives undefined proxies
        # Update only when Karabacon is in ACQUIRING state
        # TODO: Change default type in Karabacon

        # Reject first node proxy from first widget creation,
        # This contains unwanted default values. Still thinking about this.
        if proxy.path == HISTORY_PROXY_PATH:
            self._plot_history_scan(proxy)

        proxies = proxy.value

        # Add aligner results
        if hasattr(proxies, ALIGNER):
            self._controller.update_aligner_results(
                self._get_value(proxies, ALIGNER))
        if not self._first_proxy_received:
            self._first_proxy_received = True
            return
        if not self._is_scanning:
            return

        if self._scan is None:
            self._scan = self._setup_new_scan(proxy)

        # Update actual step to check for data consistency of all devices
        actual_step = self._get_value(proxies, ACTUAL_STEP)
        current_index = self._get_value(proxies, CURRENT_INDEX)
        self._scan.actual_step = actual_step
        self._scan.current_index = current_index

        # Update values of relevant devices
        is_spectrum_data = self._get_value(proxies, IS_SPECTRUM_DATA)
        if is_spectrum_data:
            source = self._scan._data_sources[0]
            spectrum_data = self._get_value(proxies, SPECTRUM_DATA)
            source.add_data_slice(spectrum_data, current_index[0])
            self._controller.update_spectrum(source.data)
        else:
            for device in self._scan.devices:
                value = self._get_value(proxies, device.name)
                device.add(value, current_index)
                self._controller.update(device)

    def _setup_new_scan(self, proxy):
        # TODO: Investigate fundamental reasons in Karabo
        if not self._is_node_proxy_valid(proxy):
            return

        # Setup new scan object
        proxies = proxy.value
        config = {}

        # Get scan parameters
        for prop in [SCAN_TYPE, STEPS, ACTUAL_STEP, START_POSITIONS,
                     STOP_POSITIONS, CURRENT_INDEX, IS_SPECTRUM_DATA]:
            config.update({prop: self._get_value(proxies, prop)})

        # Get active motor and data sources
        motor_ids = self._get_value(proxies, MOTOR_IDS)
        source_ids = self._get_value(proxies, SOURCE_IDS)
        motors = [motor for motor in MOTOR_NAMES[:len(motor_ids)]]
        sources = [source for source in SOURCE_NAMES[:len(source_ids)]]
        config.update({MOTOR_IDS: motor_ids, SOURCE_IDS: source_ids,
                       MOTORS: motors, SOURCES: sources})

        if config[IS_SPECTRUM_DATA]:
            config[MOTORS] = MOTOR_NAMES[:2]
            config[MOTOR_IDS] = ["array_index", motor_ids[0]]
            config[START_POSITIONS] = [0, config[START_POSITIONS][0]]
            config[STOP_POSITIONS] = [config[STEPS][0],
                                      config[STOP_POSITIONS][0]]

        scan = self._controller.new_scan(config)

        # Use plot  scan type
        if config[IS_SPECTRUM_DATA] or config[SCAN_TYPE] in MESHES:
            self._controller.use_heatmap_plot()
        else:
            self._controller.use_multicurve_plot()

        self._plot_available = True
        return scan

    def _plot_history_scan(self, proxy):
        if not self._is_node_proxy_valid(proxy):
            return

        # Setup new scan object
        proxies = proxy.value
        config = {}

        # Get scan parameters
        config.update({
            SCAN_TYPE: self._get_value(proxies, SCAN_TYPE),
            STEPS: self._get_value(proxies, STEPS),
            ACTUAL_STEP: 0,
            CURRENT_INDEX: [0],
            START_POSITIONS: self._get_value(proxies, START_POSITIONS),
            STOP_POSITIONS: self._get_value(proxies, STOP_POSITIONS),
            IS_SPECTRUM_DATA: self._get_value(proxies, IS_SPECTRUM_DATA)})
        # Get active motor and data sources
        motor_ids = self._get_value(proxies, MOTOR_IDS)
        source_ids = self._get_value(proxies, SOURCE_IDS)
        motors = MOTOR_NAMES[:len(motor_ids)]
        sources = SOURCE_NAMES[:len(source_ids)]
        config.update({MOTOR_IDS: motor_ids, SOURCE_IDS: source_ids,
                       MOTORS: motors, SOURCES: sources})

        scan = self._controller.new_scan(config, realtime=False)
        # User tried to plot the same historic scan. No changes in the plot
        if scan is None:
            return

        if config[SCAN_TYPE] not in MESHES:
            self._controller.use_multicurve_plot()
            for step in range(config[STEPS][0] + 1):
                scan.actual_step = step
                scan.current_index = [step]
                for device in scan.devices:
                    value = self._get_value(proxies, device.name)
                    device.add(value[step], [step])
                    self._controller.update(device)
        else:
            self._controller.use_heatmap_plot()
            index = 0
            for col in range(config[STEPS][0] + 1):
                for row in range(config[STEPS][1] + 1):
                    scan.actual_step = index
                    scan.current_index = [col, row]
                    # Update values of relevant devices
                    for device in scan.devices:
                        value = self._get_value(proxies, device.name)
                        device.add(value[index], [col, row])
                        self._controller.update(device)
                    index += 1
        self._plot_available = True

    def state_update(self, proxy):
        state = self._get_state(proxy)
        # Normally, the state should not be None
        if state is None:
            return

        self._is_scanning = False
        if state == State.ON.value:
            # # Try to plot last value
            # if self._is_scanning:
            #     self.value_update(proxy)
            # Scan is done or not started yet.
            self._controller.enable_clear_button(self._scan is not None)
            self._scan = None
        elif state == State.ACQUIRING.value:
            if self._scan is None:
                # Scan has just started.
                self._scan = self._setup_new_scan(proxy)
            self._is_scanning = True
            self._controller.enable_clear_button(False)

    @on_trait_change("_controller:_plot_double_clicked")
    def _plot_doube_clicked(self, data):
        enabled = self._get_state(self.proxy) == State.ON.value
        if enabled and not self._is_scanning and self._plot_available:
            positions = data['coord'][:len(data['aliases'])]
            text = f"Move motor(s) {data['aliases']} to {positions} ?"
            msg_box = QMessageBox(QMessageBox.Question, 'Move Motors',
                                  text, QMessageBox.Yes | QMessageBox.Cancel,
                                  parent=self.widget)
            msg_box.setDefaultButton(QMessageBox.Cancel)
            msg_box.setModal(False)
            if msg_box.exec() == QMessageBox.Yes:
                call_device_slot(WeakMethodRef(self.handle_motor_move),
                                 self.proxy.root_proxy.device_id,
                                 "requestAction",
                                 aliases=data["aliases"],
                                 positions=positions,
                                 action="moveMotors")

    def handle_motor_move(self, success, reply):
        """Handler for requestAction"""
        if not success:
            reason, details = get_reason_parts(reply)
            messagebox.show_error(reason, details=details, parent=self.widget)
        else:
            messagebox.show_information(reply["payload"]["reason"],
                                        parent=self.widget)

    def _get_state(self, proxy):
        root_proxy = proxy.root_proxy
        state = get_binding_value(root_proxy.state_binding)
        return state

    def _is_node_proxy_valid(self, proxy):
        return get_binding_value(getattr(proxy.value, SCAN_TYPE)) is not None

    def _get_value(self, proxy, prop):
        if hasattr(proxy, prop):
            return get_binding_value(getattr(proxy, prop))
