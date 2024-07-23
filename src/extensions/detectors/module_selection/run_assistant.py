#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on May 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from contextlib import contextmanager
from dataclasses import dataclass, field

from cadge.gui.api import agipd_detector
from cadge.gui.controllers import Detector
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QAction, QInputDialog, QLabel, QVBoxLayout, QWidget
from traits.api import Bool, Instance, on_trait_change

from karabo.common.api import WeakMethodRef
from karabo.native import Hash
from karabogui.api import (
    call_device_slot, get_font_size_from_dpi, get_reason_parts, messagebox)
from karabogui.binding.api import VectorHashBinding, get_binding_value
from karabogui.controllers.api import (
    BaseBindingController, is_proxy_allowed, register_binding_controller,
    with_display_type)
from karabogui.request import send_property_changes

from ...models.detectors import RunAssistantModuleSelectionModel

# -----------------------------------------------------------------------------
# Controllers


class BaseAGIPDModuleSelection(BaseBindingController):

    _detector = Instance(Detector)
    _is_waiting = Bool(default_value=False)

    # -----------------------------------------------------------------------
    # Binding methods

    def create_widget(self, parent):
        detector = agipd_detector(mode='select')
        detector.selection = self.default_detector_selection
        detector.observe(self._send_to_device, 'selection')

        self.on_trait_change(self._is_waiting_updated, '_is_waiting')

        qwidget = detector.widget.widget
        qwidget.setParent(parent)

        # Disable scrolling
        viewbox = qwidget.plotItem.getViewBox()
        viewbox.setMouseEnabled(x=False, y=False)

        # Finalize
        self._detector = detector
        return qwidget

    def value_update(self, proxy):
        # Convert device value to detector selection
        value = self.to_detector_selection(get_binding_value(proxy))

        # Use the default detector selection if there's no device value
        if value is None:
            value = self.default_detector_selection

        # Coerce value to a set
        value = set(value)

        # Avoid setting false alarms
        if self._is_waiting and value != self._detector.selection:
            return

        # Set value
        with self._waiting():
            self._detector.selection = value

    # -----------------------------------------------------------------------
    # Trait events

    def _is_waiting_updated(self, is_waiting):
        self._detector.read_only = is_waiting

    def _send_to_device(self, change):
        if self._is_waiting:
            return

        result = self.from_detector_selection(change['new'])
        if result is not None:
            self._is_waiting = True
            self.send_to_device(result)

    # -----------------------------------------------------------------------
    # Overrides

    @property
    def default_detector_selection(self):
        return set()

    def to_detector_selection(self, device_value):
        """ Converts device value to detector selection """
        return device_value or []

    def from_detector_selection(self, selection):
        """ Converts detector selection to device value """
        return list(sorted(selection))

    def send_to_device(self, selection):
        self.proxy.edit_value = selection
        send_property_changes((self.proxy,))

    # -----------------------------------------------------------------------
    # Helpers

    @contextmanager
    def _waiting(self):
        self._is_waiting = True
        try:
            yield
        finally:
            self._is_waiting = False


# -----------------------------------------------------------------------------
# Run Assistant

@dataclass
class DetectorGroup:

    instrument: str
    groupId: str
    detector_name: str

    sources: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.sources:
            self.sources = self.detector_sources(self.instrument,
                                                 self.detector_name)

    @staticmethod
    def detector_sources(instrument, detector_name, modules=range(16)):
        return [f"{instrument}_DET_{detector_name}/DET/{mod}CH0:xtdf"
                for mod in modules]


DETECTOR_GROUPS = {
    'MID: AGIPD1M': DetectorGroup(
        instrument='MID',
        groupId='AGIPD1M_XTDF',
        detector_name='AGIPD1M-1'),
    'SPB: AGIPD1M': DetectorGroup(
        instrument='SPB',
        groupId='SPB_AGIPD1M_XTDF',
        detector_name='AGIPD1M-1'),
}


@register_binding_controller(
    ui_name='Module Selection',
    klassname='RunAssistantModuleSelection',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("RunAssistant|DeviceSelection"),
    priority=0, can_show_nothing=False)
class RunAssistantModuleSelection(BaseAGIPDModuleSelection):
    """
    Module Selection for the RunAssistant.
    Currently only supports AGIPD1M detectors.
    """

    model = Instance(RunAssistantModuleSelectionModel, args=())
    detector_group = Instance(DetectorGroup)
    detector_label = Instance(QLabel)

    def create_widget(self, parent):
        widget = super().create_widget(parent)

        # Add a label on the widget
        layout = QVBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(self.detector_label)

        container = WidgetNoDoubleClick(parent)
        container.setLayout(layout)

        # Add an action to display an input dialog
        detector_action = QAction("Detector", widget)
        detector_action.triggered.connect(self._configure_detector)
        container.addAction(detector_action)

        return container

    def clear_widget(self):
        # Select all before disabling the widget
        with self._waiting():
            self._detector.selection = self.default_detector_selection
        self.widget.setEnabled(False)

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)

    @property
    def default_detector_selection(self):
        # Set the default detector selection to all modules
        return set(range(len(self.detector_group.sources)))

    def to_detector_selection(self, device_value):
        """ Converts device value to detector selection """
        if device_value is None:
            return

        # Get the sources from the supplied groupId
        sources = None
        for hsh in device_value:
            if hsh['groupId'] == self.detector_group.groupId:
                sources = hsh['sources']
                break
        else:
            return

        # We use the order of the modules in the config as the index of the
        # selection: find the module index that are not in the input sources
        selection = [index for index, source
                     in enumerate(self.detector_group.sources)
                     if source not in sources]

        return selection

    def from_detector_selection(self, selection):
        """ Converts detector selection to device value """
        # We do the inverse in this case: get the sources from the config file
        sources = [source for index, source
                   in enumerate(self.detector_group.sources)
                   if index not in selection]

        return Hash({'groupId': self.detector_group.groupId,
                     'sources': sources})

    def send_to_device(self, value):
        call_device_slot(WeakMethodRef(self.on_selection),
                         self.instanceId,
                         "requestAction",
                         action="excludedDevices",
                         groupId=value['groupId'],
                         sources=value['sources'])

    def on_selection(self, success, reply):
        if not success:
            reason, detail = get_reason_parts(reply)
            messagebox.show_error(reason, details=detail, parent=self.widget)

    @property
    def instanceId(self):
        return self.proxy.root_proxy.device_id

    def _detector_group_default(self):
        return DETECTOR_GROUPS.get(self.model.detector)

    def _detector_label_default(self):
        font = QFont()
        font.setPointSize(get_font_size_from_dpi(14))
        font.setBold(True)

        label = QLabel(self.model.detector)
        label.setFont(font)
        label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        return label

    @on_trait_change("model:detector", post_init=True)
    def _update_detector_group(self, detector):
        self.detector_group = DETECTOR_GROUPS.get(detector)
        self.value_update(self.proxy)
        self.detector_label.setText(detector)

    def _configure_detector(self):
        detectors = list(DETECTOR_GROUPS.keys())
        index = detectors.index(self.model.detector)

        location, ok = QInputDialog.getItem(self.widget,
                                            "Set detector",
                                            "Detector:",
                                            detectors, index, False)
        if not ok:
            return

        self.model.detector = location


class WidgetNoDoubleClick(QWidget):
    """Just a simple widget that catches double click events and avoid
       propagating it. This is to avoid showing default property scenes."""

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
