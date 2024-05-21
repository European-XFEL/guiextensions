#############################################################################
# Author: Ivars Karpics
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from pathlib import Path

from qtpy import uic
from qtpy.QtCore import QStringListModel, Qt, Signal, Slot
from qtpy.QtWidgets import QAbstractItemView, QCompleter, QDialog

from karabogui.api import (
    FloatBinding, IntBinding, PipelineOutputBinding, SignalBlocker,
    VectorNumberBinding, WidgetNodeBinding)
from karabogui.request import get_topology, onSchemaUpdate


class ScantoolDeviceDialog(QDialog):

    addDevicesSignal = Signal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.devices = []

        uic.loadUi(str(Path(__file__).parent / "device_dialog.ui"), self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.device_listwidget.setSelectionMode(
            QAbstractItemView.ContiguousSelection)

        self.completer = QCompleter(parent=parent)
        self.completer.setCaseSensitivity(False)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.prop_cbox.setCompleter(self.completer)

        self.filter_ledit.textEdited.connect(self._filter_text_edited)
        self.clear_filter_bt.clicked.connect(self._clear_filter)
        self.add_devices_bt.clicked.connect(self._add_devices)
        self.device_type_cbox.currentIndexChanged.connect(
            self._device_type_changed)
        self.device_listwidget.itemDoubleClicked.connect(
            self._device_item_doubleclicked)
        self.device_listwidget.itemSelectionChanged.connect(
            self._device_selection_changed)

    def init_devices(self):
        self.devices.clear()
        topo_hash = get_topology()._system_hash
        if (topo_hash is None or topo_hash.get("device") is None):
            return

        self.devices = [dev_id
                        for dev_id, _, _ in topo_hash["device"].iterall()]

    def show(self):
        self.init_devices()
        self.display_devices()
        super().show()

    @Slot(str)
    def _filter_text_edited(self, text):
        self.display_devices(text)

    @Slot()
    def _clear_filter(self):
        self.filter_ledit.setText("")
        self.display_devices()

    @Slot()
    def _add_devices(self):
        device_type = self.device_type_cbox.currentText()
        devices = []
        for device in self.device_listwidget.selectedItems():
            device_id = device.text()
            alias = device_id.split("/")[-1]
            device_descr = [alias, device_id]
            if device_type == "Motors":
                device_descr.append("default")
            elif device_type == "Sources":
                device_descr.append(self.prop_cbox.currentText())
            devices.append(device_descr)
        self.addDevicesSignal.emit(device_type, devices)

    @Slot()
    def _device_type_changed(self):
        self._populate_device_attributes()

    @Slot()
    def _device_selection_changed(self):
        self._populate_device_attributes()

    @Slot()
    def _device_item_doubleclicked(self):
        self._add_devices()

    def _populate_device_attributes(self):
        def _schema_handler():
            properties = []
            for key in proxy.binding.value:
                bind = getattr(proxy.binding.value, key)
                if isinstance(bind, (IntBinding,
                                     FloatBinding,
                                     VectorNumberBinding)):
                    properties.append(key)
                elif isinstance(bind, (WidgetNodeBinding,
                                       PipelineOutputBinding)):
                    properties.append(f"{key}.")
                    # I could not figure out how to add all node child items
                    # to the list of available properties
                    # bind.children_names is always empty
            self.fill_properties_combo(properties)

        selected_items = self.device_listwidget.selectedItems()
        self.add_devices_bt.setEnabled(len(selected_items))
        if not selected_items:
            self.fill_properties_combo([])
            return

        device_type = self.device_type_cbox.currentText()
        if device_type == "Motors":
            self.fill_properties_combo(["default"])
        else:
            proxy = get_topology().get_device(selected_items[0].text())
            onSchemaUpdate(proxy, _schema_handler, request=True)

    def fill_properties_combo(self, properties):
        self.prop_cbox.clear()
        with SignalBlocker(self.prop_cbox):
            self.completer.setModel(
                QStringListModel(properties, self.completer))
            self.prop_cbox.addItems(properties)
            self.prop_cbox.setCurrentIndex(0)

    def display_devices(self, filter_text=""):
        self.device_listwidget.clear()
        for dev_id in self.devices:
            if filter_text.lower() in dev_id.lower():
                self.device_listwidget.addItem(dev_id)
