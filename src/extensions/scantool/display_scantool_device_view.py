#############################################################################
# Author: Ivars Karpics
# Created July 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections import OrderedDict
from enum import Enum

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import (
    QHeaderView, QMessageBox, QTreeWidgetItem, QVBoxLayout, QWidget)
from traits.api import Bool, Dict, Instance, String, WeakRef

from karabo.native import Hash, HashList
from karabogui.api import (
    BaseBindingController, PropertyProxy, VectorHashBinding, get_binding_value,
    is_proxy_allowed, register_binding_controller, with_display_type)

from ..models.api import ScantoolDeviceViewModel
from .dialogs.device_dialog import ScantoolDeviceDialog
from .widgets import ButtonToolbar, DeviceTreeWidget


class DeviceTypes(Enum):
    MOTORS = "motors"
    SOURCES = "sources"
    TRIGGERS = "triggers"


DEVICE_ATTRIBUTES_MAP = OrderedDict([
    (DeviceTypes.MOTORS.value, ["alias", "deviceId", "axis"]),
    (DeviceTypes.SOURCES.value, ["alias", "deviceId", "source"]),
    (DeviceTypes.TRIGGERS.value, ["alias", "deviceId"])])
HEADER_LABELS = ["Alias", "Device", "Axis/Source"]
BRUSH_NOT_ACTIVE = QBrush(Qt.white)
BRUSH_GROUP = QBrush(QColor(240, 240, 240))
BRUSH_ACTIVE = QBrush(QColor(200, 230, 255))


class DeviceEnvironmentWidget(QWidget):

    deviceEnvChanged = Signal(str, list)

    def __init__(self, parent):
        super().__init__(parent)

        self._toolbar = ButtonToolbar(parent=self)
        self._device_tree = DeviceTreeWidget(parent=self)
        self._device_groups = {}

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._toolbar)
        main_layout.addWidget(self._device_tree)

        header = self._device_tree.header()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self._device_tree.setColumnCount(len(HEADER_LABELS))
        self._device_tree.setHeaderLabels(HEADER_LABELS)

        for dev_type in DEVICE_ATTRIBUTES_MAP.keys():
            tree_item = QTreeWidgetItem([dev_type.title()])
            self._device_tree.addTopLevelItem(tree_item)
            self._device_groups[dev_type] = tree_item

        self._device_tree.itemSelectionChanged.connect(self.tree_item_selected)
        self._device_tree.itemChanged.connect(self.tree_item_changed)
        self._toolbar.buttonClicked.connect(self.toolbar_button_clicked)

        self._device_dialog = ScantoolDeviceDialog(parent=self)
        self._device_dialog.addDevicesSignal.connect(
            self._add_devices_from_dialog)

    @Slot(str)
    def toolbar_button_clicked(self, button_type):
        if button_type == "device_dialog":
            self._device_dialog.show()
        elif button_type == "add":
            self._add_clicked()
        elif button_type == "copy":
            self._copy_clicked()
        elif button_type == "up":
            self._up_clicked()
        elif button_type == "down":
            self._down_clicked()
        elif button_type == "sort":
            self._sort_clicked()
        elif button_type == "remove":
            self._remove_clicked()
        elif button_type == "remove_all":
            self._remove_all_clicked()

    @Slot()
    def tree_item_selected(self):
        selected_item = None
        if self._device_tree.selectedItems():
            selected_item = self._device_tree.selectedItems()[0]
        self._toolbar.update_button_states(selected_item)

    @Slot(QTreeWidgetItem)
    def tree_item_changed(self, item):
        self.emit_device_env_changed(item.parent())

    def refresh_device_group(self, proxy_path, devices):
        self._device_tree.setUpdatesEnabled(False)

        path = proxy_path.split(".")[-1]
        group_item = self._device_groups[path]
        for index in reversed(range(group_item.childCount())):
            group_item.removeChild(group_item.child(index))

        for device in devices:
            descr = [device[col] for col in DEVICE_ATTRIBUTES_MAP[path]]
            tree_item = QTreeWidgetItem(descr)
            tree_item.setFlags(tree_item.flags() | Qt.ItemIsEditable)
            tree_item.setCheckState(
                0, Qt.Checked if device.get("active") else Qt.Unchecked)
            brush = BRUSH_ACTIVE if device.get("active") else BRUSH_NOT_ACTIVE
            for col in range(len(descr)):
                tree_item.setBackground(col, brush)
            group_item.addChild(tree_item)

        group_item.setExpanded(True)
        group_item.setSelected(False)
        self._device_tree.setUpdatesEnabled(True)

    def emit_device_env_changed(self, group_item):
        devices = HashList()
        for proxy_path, tree_item in self._device_groups.items():
            if tree_item is group_item:
                break

        for child_index in range(group_item.childCount()):
            child = group_item.child(child_index)
            device = Hash({key: child.text(row)
                           for row, key in enumerate(
                               DEVICE_ATTRIBUTES_MAP[proxy_path])})
            device["active"] = child.checkState(0) == Qt.Checked
            devices.append(device)

        selected_item = None
        if self._device_tree.selectedItems():
            selected_item = self._device_tree.selectedItems()[0]
        self._toolbar.update_button_states(selected_item)
        self.deviceEnvChanged.emit(proxy_path, devices)

    def add_new_item(self, group_item, device):
        new_item = QTreeWidgetItem(device)
        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)

        current_item = self._device_tree.currentItem()
        if current_item is group_item:
            group_item.addChild(new_item)
        else:
            index = group_item.indexOfChild(current_item)
            group_item.insertChild(index + 1, new_item)
        self.emit_device_env_changed(group_item)

    def _add_devices_from_dialog(self, device_type, devices):
        if devices:
            for group_item in self._device_groups.values():
                if group_item.text(0) == device_type:
                    for device in devices:
                        self.add_new_item(group_item, device)
                    self.emit_device_env_changed(group_item)
                    break

    def _add_clicked(self):
        item = self._device_tree.currentItem()
        if item is None:
            # No item selected, add to motors
            group_item = self._device_tree.topLevelItem(0)
        else:
            group_item = item.parent() if item.parent() else item

        device = ["ALIAS", "DEVICE_ID", "default"]
        self.add_new_item(group_item, device)

    def _copy_clicked(self):
        item = self._device_tree.currentItem()
        group_item = item.parent()
        index = group_item.indexOfChild(item)
        new_item = item.clone()
        group_item.insertChild(index + 1, new_item)
        self._device_tree.setCurrentItem(new_item)
        self.emit_device_env_changed(group_item)

    def _up_clicked(self):
        self._move_current_item(-1)

    def _down_clicked(self):
        self._move_current_item(1)

    def _move_current_item(self, direction):
        item = self._device_tree.currentItem()
        group_item = item.parent()
        index = group_item.indexOfChild(item)
        group_item.takeChild(index)
        group_item.insertChild(index + direction, item)
        self._device_tree.setCurrentItem(item)
        self.emit_device_env_changed(group_item)

    def _sort_clicked(self):
        for group_item in self._device_groups.values():
            unchecked_items = []
            for index in reversed(range(group_item.childCount())):
                if group_item.child(index).checkState(0) != Qt.Checked:
                    unchecked_items.append(group_item.takeChild(index))
            # As we removed items in the reverse order, we have to put them
            # back in the reverse order
            for item in reversed(unchecked_items):
                group_item.addChild(item)
            self.emit_device_env_changed(group_item)

    def _remove_clicked(self):
        item = self._device_tree.currentItem()
        group_item = item.parent()
        group_item.removeChild(item)
        self.emit_device_env_changed(group_item)

    def _remove_all_clicked(self):
        reply = QMessageBox.question(
            self._device_tree.parent(), "Remove Devices",
            "Are you sure you want to remove all devices?",
            (QMessageBox.Yes | QMessageBox.No), QMessageBox.No)
        if reply == QMessageBox.Yes:
            for group_item in self._device_groups.values():
                for index in reversed(range(group_item.childCount())):
                    group_item.takeChild(index)
            self.emit_device_env_changed(group_item)


@register_binding_controller(
    ui_name="Scantool Device View",
    klassname="Scantool-Device-View",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("ScantoolDeviceView"),
    can_show_nothing=True, can_edit=True)
class ScantoolDeviceView(BaseBindingController):
    # The scene model class used by this controller
    model = Instance(ScantoolDeviceViewModel, args=())
    # Private traits
    _data_env_proxy = Instance(PropertyProxy)
    _trigger_env_proxy = Instance(PropertyProxy)
    _group_refs = Dict(String, WeakRef(QTreeWidgetItem))
    _is_editing = Bool(False)
    _is_updating = Bool(False)

    def create_widget(self, parent):
        widget = DeviceEnvironmentWidget(parent=parent)
        widget.deviceEnvChanged.connect(self.device_env_changed)
        return widget

    def add_proxy(self, proxy):
        # motorEnv should be defined as first proxy
        if DeviceTypes.SOURCES.value in proxy.path:
            if self._data_env_proxy is None:
                self._data_env_proxy = proxy
                return True
        elif DeviceTypes.TRIGGERS.value in proxy.path:
            if self._trigger_env_proxy is None:
                self._trigger_env_proxy = proxy
                return True
        return False

    def value_update(self, proxy):
        devices = get_binding_value(proxy, None)
        if devices is None or self._is_editing:
            return

        self._is_updating = True
        self.widget.refresh_device_group(proxy.path, devices)
        self._is_updating = False

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)

    def device_env_changed(self, proxy_path, devices):
        if self._is_updating:
            return

        self._is_editing = True
        for proxy in self.proxies:
            if proxy_path in proxy.path:
                proxy.edit_value = devices
                break
        self._is_editing = False
