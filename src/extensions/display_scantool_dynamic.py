#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from traits.api import Bool, Instance, Int

from karabo.common.states import State
from karabogui.binding.api import get_binding_value, WidgetNodeBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)

from .models.simple import ScantoolBaseModel

from .scantool.const import (
    ACTUAL_STEP, ASCANS, CSCANS, CURRENT_INDEX, DSCANS, NUM_DATA_SOURCES,
    SCAN_TYPE, START_POSITIONS, STEPS, STOP_POSITIONS)
from .scantool.controller import ScanController
from .scantool.data.scan import Scan


@register_binding_controller(
    ui_name='Scantool Base Widget',
    klassname='Scantool-Base',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Scantool-Base'),
    priority=0, can_show_nothing=False)
class ScantoolDynamicWidget(BaseBindingController):
    model = Instance(ScantoolBaseModel, args=())

    _controller = Instance(ScanController)
    # Scan contains the scan parameters, device objects
    _scan = Instance(Scan)

    _is_scanning = Bool(False)
    _num_received_proxy = Int(0)

    def create_widget(self, parent):
        self._controller = ScanController(parent=parent)
        self._controller.add_data_selection()
        return self._controller.widget

    def value_update(self, proxy):
        # This is for initialization.
        # binding_update only gives undefined proxies
        # Update only when Karabacon is in ACQUIRING state

        # TODO: Change default type in Karabacon

        # Reject first two node proxy from first widget creation,
        # This contains unwanted default values. Still thinking about this.
        if self._num_received_proxy < 2:
            self._num_received_proxy += 1
            return

        if not self._is_scanning:
            return

        if self._scan is None:
            self._scan = self._setup_new_scan(proxy)

        # Update actual step to check for data consistency of all devices
        proxies = proxy.value
        actual_step = get_binding_value(getattr(proxies, ACTUAL_STEP))
        current_index = get_binding_value(getattr(proxies, CURRENT_INDEX))
        self._scan.actual_step = actual_step
        self._scan.current_index = current_index

        # Update values of relevant devices
        for device in self._scan.devices:
            value = get_binding_value(getattr(proxies, device.name))
            device.add(value, current_index)
            self._controller.update(device)

    def _setup_new_scan(self, proxy):
        # TODO: Investigate fundamental reasons in Karabo
        if not self._is_node_proxy_valid(proxy):
            return

        # Setup new scan object
        proxies = proxy.value
        config = {}
        for prop in [SCAN_TYPE, NUM_DATA_SOURCES, STEPS, ACTUAL_STEP,
                     START_POSITIONS, STOP_POSITIONS, CURRENT_INDEX]:
            config.update({prop: get_binding_value(getattr(proxies, prop))})

        scan = self._controller.new_scan(config)

        # Use plot wrt scan type
        if config[SCAN_TYPE] in ASCANS + DSCANS + CSCANS:
            self._controller.use_multicurve_plot()
        else:
            self._controller.use_heatmap_plot()

        return scan

    def state_update(self, proxy):
        state = self._get_state(proxy)
        # Normally, the state should not be None
        if state is None:
            return

        if state == State.ON.value:
            # Scan is done or not started yet.
            self._scan = None
            self._is_scanning = False
        elif state == State.ACQUIRING.value and self._scan is None:
            # Scan has just started.
            self._scan = self._setup_new_scan(proxy)
            self._is_scanning = True

    def _get_state(self, proxy):
        root_proxy = proxy.root_proxy
        state = get_binding_value(root_proxy.state_binding)
        return state

    def _is_node_proxy_valid(self, proxy):
        return get_binding_value(getattr(proxy.value, SCAN_TYPE)) is not None
