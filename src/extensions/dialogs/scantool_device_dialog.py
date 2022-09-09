#############################################################################
# Author: Ivars Karpics
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from qtpy import uic
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QAbstractItemView, QDialog

from karabogui.request import get_topology

from .utils import get_dialog_ui


class ScantoolDeviceDialog(QDialog):

    addDevicesSignal = Signal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        uic.loadUi(get_dialog_ui("device_dialog.ui"), self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.device_listwidget.setSelectionMode(
            QAbstractItemView.ContiguousSelection)

        self.filter_ledit.textEdited.connect(self._filter_text_edited)
        self.clear_filter_bt.clicked.connect(self._clear_filter)
        self.add_devices_bt.clicked.connect(self._add_devices)
        self.device_type_cbox.currentIndexChanged.connect(
            self._device_type_changed)
        self.device_listwidget.itemDoubleClicked.connect(
            self._device_item_doubleclicked)
        self.display_devices()

    def _filter_text_edited(self, text):
        self.display_devices(text)

    def _clear_filter(self):
        self.filter_ledit.setText("")
        self.display_devices()

    def _add_devices(self):
        device_type = self.device_type_cbox.currentText()
        devices = []
        for device in self.device_listwidget.selectedItems():
            device_id = device.text()
            alias = device_id.split("/")[-1]
            device_dict = {"alias": alias,
                           "deviceId": device_id}
            if device_type == "Motors":
                device_dict["axis"] = self.prop_ledit.text()
            elif device_type == "Sources":
                device_dict["source"] = self.prop_ledit.text()
            devices.append(device_dict)
        self.addDevicesSignal.emit(device_type, devices)

    def _device_type_changed(self, index):
        self.display_devices()

    def _device_item_doubleclicked(self, item):
        self._add_devices()

    def display_devices(self, filter_text=""):
        topology = get_topology()
        self.device_listwidget.clear()

        if (topology._system_hash is None or
                topology._system_hash.get("device") is None):
            return

        for dev_id, _, attrs in topology._system_hash["device"].iterall():
            if filter_text:
                if filter_text in dev_id:
                    self.device_listwidget.addItem(dev_id)
            else:
                self.device_listwidget.addItem(dev_id)
