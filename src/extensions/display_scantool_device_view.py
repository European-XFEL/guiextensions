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
from karabogui.binding.api import (
    PropertyProxy, VectorHashBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.request import send_property_changes

from .dialogs.scantool_device_dialog import ScantoolDeviceDialog
from .models.api import ScantoolDeviceViewModel
from .scantool.device_tree import ButtonToolbar, DeviceTreeWidget

HEADER_LABELS = ["Alias", "Device", "Axis/Source"]
DEVICE_PROXY_MAP = OrderedDict()
DEVICE_PROXY_MAP["motorEnv"] = {"title": "Motors",
                                "rows": ["alias", "deviceId", "axis"]}
DEVICE_PROXY_MAP["dataEnv"] = {"title": "Sources",
                               "rows": ["alias", "deviceId", "source"]}
DEVICE_PROXY_MAP["triggerEnv"] = {"title": "Triggers",
                                  "rows": ["alias", "deviceId"]}

BRUSH_NOT_ACTIVE = QBrush(Qt.white)
BRUSH_GROUP = QBrush(QColor(240, 240, 240))
BRUSH_ACTIVE = QBrush(QColor(200, 230, 255))
COLUMN_COUNT = 3


@register_binding_controller(
    ui_name='Scantool Device View',
    klassname='Scantool-Device-View',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type('ScantoolDeviceView'),
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
    _changed_groups = Dict(String, Bool)
    _is_editing = Bool(False)
    _is_updating = Bool(False)

    def create_widget(self, parent):
        main_widget = QWidget(parent=parent)
        self._treewidget = DeviceTreeWidget(parent=main_widget)
        header = self._treewidget.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self._toolbar = ButtonToolbar(self._treewidget, main_widget)

        self._treewidget.setColumnCount(COLUMN_COUNT)
        self._treewidget.setHeaderLabels(HEADER_LABELS)
        for dev_proxy_path, dev_type in DEVICE_PROXY_MAP.items():
            dev_group_item = QTreeWidgetItem([dev_type["title"]])
            self._treewidget.addTopLevelItem(dev_group_item)
            self._group_refs[dev_proxy_path] = dev_group_item
            self._changed_groups[dev_proxy_path] = False

        self._treewidget.itemChanged.connect(self._item_changed)
        self._toolbar.addButtonClicked.connect(self._add_devices)
        self._toolbar.applyButtonClicked.connect(self._apply_changes)
        self._toolbar.removeAllButtonClicked.connect(self._remove_devices)

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
        if proxy.path == "dataEnv":
            if self._data_env_proxy is None:
                self._data_env_proxy = PropertyProxy(
                    root_proxy=proxy.root_proxy,
                    path=proxy.path)
                return True
        elif proxy.path == "triggerEnv":
            if self._trigger_env_proxy is None:
                self._trigger_env_proxy = PropertyProxy(
                    root_proxy=proxy.root_proxy,
                    path=proxy.path)
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

        self._toolbar.set_apply_button_enabled(False)
        self._is_updating = False
        self._treewidget.setUpdatesEnabled(True)

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

    def _item_changed(self, item):
        if self.proxy.binding is None or self._is_updating:
            return

        self._is_editing = True

        group_item = item.parent()
        for key, value in self._group_refs.items():
            if value == group_item:
                self._changed_groups[key] = True

        self._treewidget.setUpdatesEnabled(True)
        self._toolbar.set_apply_button_enabled(True)
        self._is_updating = False
        self._is_editing = False

    def _add_devices(self):
        self._device_dialog.show()

    def _add_devices_from_dialog(self, device_type, devices):
        if devices:
            for proxy_path, group_item in self._group_refs.items():
                if group_item.text(0) == device_type:
                    for device in devices:
                        self.add_device_tree_item(device,
                                                  group_item,
                                                  proxy_path)
                    self._changed_groups[proxy_path] = True
                    self._toolbar.set_apply_button_enabled(True)
                    break

    def _remove_devices(self):
        reply = QMessageBox.question(
            self._treewidget.parent(), "Remove Devices",
            "Are you sure you want to remove all devices?",
            (QMessageBox.Yes | QMessageBox.No), QMessageBox.No)
        if reply == QMessageBox.Yes:
            for group_item in self._group_refs.values():
                for index in reversed(range(group_item.childCount())):
                    group_item.takeChild(index)
            self._toolbar.set_apply_button_enabled(True)

    def _apply_changes(self):
        proxies = []
        for proxy_path, group_item in self._group_refs.items():
            if self._changed_groups[proxy_path]:
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
                proxies.append(proxy)

        # This do not work. Proxy references differ
        # proxies = [proxy for proxy in self.proxies
        #           if proxy.edit_value is not None]

        if proxies:
            send_property_changes(proxies)

        self._toolbar.set_apply_button_enabled(False)
        self._changed_groups = dict.fromkeys(self._changed_groups, False)
