#############################################################################
# Author: Ivars Karpics
# Created July 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections import OrderedDict

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import (
    QHeaderView, QMessageBox, QSizePolicy, QTreeWidgetItem, QVBoxLayout,
    QWidget)
from traits.api import Bool, Dict, Instance, String, WeakRef

from karabo.native import Hash, HashList
from karabogui.api import is_proxy_allowed
from karabogui.binding.api import (
    PropertyProxy, VectorHashBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)

from .dialogs.scantool_device_dialog import ScantoolDeviceDialog
from .models.api import ScantoolDeviceViewModel
from .scantool.const import BUTTON_DEV_DIALOG, BUTTON_REMOVE_ALL, BUTTON_SORT
from .scantool.device_tree import ButtonToolbar, DeviceTreeWidget

HEADER_LABELS = ["Alias", "Device", "Axis/Source"]
MOTORS_PROXY_PATH = "deviceEnv.motors"
SOURCES_PROXY_PATH = "deviceEnv.sources"
TRIGGERS_PROXY_PATH = "deviceEnv.triggers"

DEVICE_PROXY_MAP = OrderedDict()
DEVICE_PROXY_MAP[MOTORS_PROXY_PATH] = {
    "title": "Motors", "rows": ["alias", "deviceId", "axis"]}
DEVICE_PROXY_MAP[SOURCES_PROXY_PATH] = {
    "title": "Sources", "rows": ["alias", "deviceId", "source"]}
DEVICE_PROXY_MAP[TRIGGERS_PROXY_PATH] = {
    "title": "Triggers", "rows": ["alias", "deviceId"]}

BRUSH_NOT_ACTIVE = QBrush(Qt.white)
BRUSH_GROUP = QBrush(QColor(240, 240, 240))
BRUSH_ACTIVE = QBrush(QColor(200, 230, 255))
COLUMN_COUNT = 3


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
    _device_dialog = Instance(ScantoolDeviceDialog)
    _treewidget = WeakRef(DeviceTreeWidget)
    _toolbar = WeakRef(ButtonToolbar)
    _data_env_proxy = Instance(PropertyProxy)
    _trigger_env_proxy = Instance(PropertyProxy)
    _group_refs = Dict(String, WeakRef(QTreeWidgetItem))
    _is_editing = Bool(False)
    _is_updating = Bool(False)

    def create_widget(self, parent):
        main_widget = QWidget(parent=parent)
        self._treewidget = DeviceTreeWidget(parent=main_widget)
        header = self._treewidget.header()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self._toolbar = ButtonToolbar(self._treewidget, main_widget)

        self._treewidget.setColumnCount(COLUMN_COUNT)
        self._treewidget.setHeaderLabels(HEADER_LABELS)
        for dev_proxy_path, dev_type in DEVICE_PROXY_MAP.items():
            dev_group_item = QTreeWidgetItem([dev_type["title"]])
            self._treewidget.addTopLevelItem(dev_group_item)
            self._group_refs[dev_proxy_path] = dev_group_item

        self._treewidget.itemChanged.connect(self._item_changed)
        self._toolbar.buttonClicked.connect(self._toolbar_button_clicked)

        self._device_dialog = ScantoolDeviceDialog(parent=self.widget)
        self._device_dialog.addDevicesSignal.connect(
            self._add_devices_from_dialog)

        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(self._toolbar)
        main_layout.addWidget(self._treewidget)

        main_widget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                  QSizePolicy.MinimumExpanding)

        return main_widget

    def add_proxy(self, proxy):
        # motorEnv should be defined as first proxy
        if proxy.path == SOURCES_PROXY_PATH:
            if self._data_env_proxy is None:
                self._data_env_proxy = proxy
                return True
        elif proxy.path == TRIGGERS_PROXY_PATH:
            if self._trigger_env_proxy is None:
                self._trigger_env_proxy = proxy
                return True
        return False

    def value_update(self, proxy):
        if self._is_editing:
            return

        devices = get_binding_value(proxy, None)
        group_item = self._group_refs.get(proxy.path)

        if devices is None or group_item is None:
            return

        self._is_updating = True
        self._treewidget.setUpdatesEnabled(False)
        for index in reversed(range(group_item.childCount())):
            group_item.removeChild(group_item.child(index))

        for device in devices:
            self.add_device_tree_item(device, group_item, proxy.path)
        group_item.setExpanded(True)
        group_item.setSelected(False)

        self._is_updating = False
        self._treewidget.setUpdatesEnabled(True)

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)

    def add_device_tree_item(self, device, group_item, proxy_path):
        rows = [device[row] for row in DEVICE_PROXY_MAP[proxy_path]["rows"]]
        tree_item = QTreeWidgetItem(rows)
        tree_item.setFlags(tree_item.flags() | Qt.ItemIsEditable)
        tree_item.setCheckState(
            0, Qt.Checked if device.get("active") else Qt.Unchecked)
        brush = BRUSH_ACTIVE if device.get("active") else BRUSH_NOT_ACTIVE
        for col in range(COLUMN_COUNT):
            tree_item.setBackground(col, brush)
        group_item.addChild(tree_item)

        self._apply_changes()

    def _item_changed(self, item):
        if self.proxy.binding is None or self._is_updating:
            return

        self._is_editing = True
        self._apply_changes()
        self._is_updating = False
        self._is_editing = False

    def _toolbar_button_clicked(self, button_type):
        if button_type == BUTTON_DEV_DIALOG:
            self._device_dialog.show()
        elif button_type == BUTTON_SORT:
            self._sort_devices()
        elif button_type == BUTTON_REMOVE_ALL:
            self._remove_devices()
        else:
            self._apply_changes()

    def _add_devices_from_dialog(self, device_type, devices):
        if devices:
            for proxy_path, group_item in self._group_refs.items():
                if group_item.text(0) == device_type:
                    for device in devices:
                        self.add_device_tree_item(device,
                                                  group_item,
                                                  proxy_path)
                    self._apply_changes()
                    break

    def _sort_devices(self):
        for group_item in self._group_refs.values():
            unchecked_items = []
            for index in reversed(range(group_item.childCount())):
                if group_item.child(index).checkState(0) != Qt.Checked:
                    unchecked_items.append(group_item.takeChild(index))
            # As we removed items in the reverse order, we have to put them
            # back in the reverse order
            for item in reversed(unchecked_items):
                group_item.addChild(item)
        self._apply_changes()

    def _remove_devices(self):
        reply = QMessageBox.question(
            self._treewidget.parent(), "Remove Devices",
            "Are you sure you want to remove all devices?",
            (QMessageBox.Yes | QMessageBox.No), QMessageBox.No)
        if reply == QMessageBox.Yes:
            for group_item in self._group_refs.values():
                for index in reversed(range(group_item.childCount())):
                    group_item.takeChild(index)
            self._apply_changes()

    def _apply_changes(self):
        if self._is_updating:
            return

        for proxy_path, group_item in self._group_refs.items():
            for proxy in self.proxies:
                if proxy.path == proxy_path:
                    break

            devices = HashList()
            for child_index in range(group_item.childCount()):
                child = group_item.child(child_index)
                device = Hash()
                for row, key in enumerate(
                        DEVICE_PROXY_MAP[proxy_path]["rows"]):
                    device[key] = child.text(row)
                device["active"] = child.checkState(0) == Qt.Checked
                devices.append(device)

            proxy.edit_value = devices
