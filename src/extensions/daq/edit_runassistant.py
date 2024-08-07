#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on November 29, 2023
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import QModelIndex, QSortFilterProxyModel, Qt
from qtpy.QtGui import QBrush, QFont, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView, QDialog, QHeaderView, QMenu, QSizePolicy, QTreeView,
    QVBoxLayout, QWidget)
from traits.api import Bool, Instance, WeakRef

from karabo.common.api import WeakMethodRef
from karabo.native import Hash
from karabogui.api import (
    BaseBindingController, PropertyProxy, VectorHashBinding, call_device_slot,
    get_binding_value, get_editor_value, get_reason_parts,
    get_scene_from_server, is_proxy_allowed, messagebox,
    register_binding_controller, with_display_type)

from ..models.api import EditableAssistantOverviewModel
from .selection_dialog import SelectionDialog
from .toolbar import SearchBar

HEADER_LABELS = ["Selected", "Group"]
KEY_GROUP_ID = "groupId"
KEY_SELECTED = "selected"
KEY_NAME = "name"
DEVICES_DISPLAY_TYPE = "RunAssistant|GroupDevices"
OVERVIEW_DISPLAY_TYPE = "RunAssistant|Overview"
SELECTION_DISPLAY_TYPE = "RunAssistant|DeviceSelection"


@register_binding_controller(
    ui_name="RunAssistant Overview",
    klassname="RunAssistantOverview",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type(OVERVIEW_DISPLAY_TYPE),
    can_edit=True, priority=40, can_show_nothing=False)
class RunAssistantEdit(BaseBindingController):
    model = Instance(EditableAssistantOverviewModel, args=())

    _is_editing = Bool(False)
    _expanded = Bool(False)
    _group_devices = Instance(PropertyProxy)
    _excluded_devices = Instance(PropertyProxy)

    tree_widget = WeakRef(QTreeView)
    toolbar = WeakRef(QWidget)

    def create_widget(self, parent):
        widget = QWidget(parent)
        tree_widget = QTreeView(parent=parent)
        tree_widget.setFocusPolicy(Qt.StrongFocus)
        tree_widget.setUniformRowHeights(True)
        tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        tree_widget.customContextMenuRequested.connect(self.context_menu)

        item_model = QStandardItemModel(parent=widget)
        item_model.setHorizontalHeaderLabels(HEADER_LABELS)
        item_model.itemChanged.connect(self.on_item_edit)

        header = tree_widget.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.sectionDoubleClicked.connect(self.on_double_click_header)

        tree_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        filter_model = QSortFilterProxyModel()
        filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        filter_model.setFilterRole(Qt.DisplayRole)
        filter_model.setFilterKeyColumn(1)
        filter_model.setRecursiveFilteringEnabled(True)
        filter_model.setSourceModel(item_model)

        tree_widget.setModel(filter_model)
        self.tree_widget = tree_widget
        self.toolbar = SearchBar(widget)
        self.toolbar.setView(tree_widget)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.tree_widget)

        widget.setSizePolicy(QSizePolicy.MinimumExpanding,
                             QSizePolicy.MinimumExpanding)

        widget.setFocusProxy(tree_widget)

        return widget

    def add_proxy(self, proxy):
        if proxy.binding is None:
            return True

        display_type = proxy.binding.display_type
        if (display_type == DEVICES_DISPLAY_TYPE
                and self._group_devices is None):
            self._group_devices = proxy
            return True
        elif (display_type == SELECTION_DISPLAY_TYPE
              and self._excluded_devices is None):
            self._excluded_devices = proxy
            return True

        return False

    def binding_update(self, proxy):
        if proxy is self.proxy:
            return
        self.add_proxy(proxy)

    def value_update(self, proxy):
        # Avoid messing with the item model when the user checks an item
        if proxy is self._group_devices or self._is_editing:
            return

        # We reset on every value update!
        self._expanded = False
        self._is_editing = True

        def create_group(group_h, parent_item):
            identifier = group_h[KEY_GROUP_ID]
            group_item = QStandardItem(identifier)
            group_item.setData(group_h[KEY_NAME], Qt.UserRole)
            group_item.setEditable(False)

            selected = Qt.Checked if group_h[KEY_SELECTED] else Qt.Unchecked
            selection_item = QStandardItem()
            selection_item.setCheckable(True)
            selection_item.setCheckState(selected)
            selection_item.setEditable(False)
            parent_item.appendRow([selection_item, group_item])

            modified = False
            if self._group_devices:
                devices, excluded = self.get_group_devices(identifier)
                for source in devices:
                    spacer = QStandardItem()
                    spacer.setEditable(False)
                    add_item = QStandardItem(source)
                    if source in excluded:
                        add_item.setForeground(QBrush(Qt.gray))
                        modified = True
                    add_item.setEditable(False)
                    selection_item.appendRow([spacer, add_item])
            if modified:
                font = QFont()
                font.setBold(True)
                group_item.setFont(font)

        self.tree_widget.setUpdatesEnabled(False)
        # Clear item_model before updating
        item_model = self.sourceModel()
        item_model.removeRows(0, item_model.rowCount())

        root_item = item_model.invisibleRootItem()
        for entry in get_editor_value(self.proxy, []):
            create_group(entry, root_item)

        self.tree_widget.setUpdatesEnabled(True)
        self._is_editing = False

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)

    # Slots
    # ----------------------------------------------------------------------

    def sourceModel(self):
        return self.tree_widget.model().sourceModel()

    def filterModel(self):
        return self.tree_widget.model()

    def get_group_devices(self, name):
        devices = get_binding_value(self._group_devices, [])
        for group in devices:
            if group[KEY_GROUP_ID] == name:
                devices = group["sources"]

        excluded = []
        if self._excluded_devices:
            sources = get_binding_value(self._excluded_devices, [])
            for group in sources:
                if group[KEY_GROUP_ID] == name:
                    excluded = group["sources"]
                    break

        return devices, excluded

    def create_edit_value(self):
        values = []
        item_model = self.sourceModel()
        for i in range(item_model.rowCount(QModelIndex())):
            check_item = item_model.item(i, 0)
            checked = check_item.checkState() == Qt.Checked
            item = item_model.item(i, 1)
            item_hash = Hash(KEY_GROUP_ID, item.text(),
                             KEY_NAME, item.data(Qt.UserRole),
                             KEY_SELECTED, checked)
            values.append(item_hash)

        return values

    # Slots
    # ----------------------------------------------------------------------

    def on_double_click_header(self):
        if self._expanded:
            self.tree_widget.collapseAll()
        else:
            self.tree_widget.expandAll()
        self._expanded = not self._expanded

    def on_item_edit(self, item):
        if self.proxy.binding is None or self._is_editing:
            return

        self._is_editing = True
        self.proxy.edit_value = self.create_edit_value()
        self._is_editing = False

    # Action Interface
    # ----------------------------------------------------------------------

    @property
    def instanceId(self):
        return self.proxy.root_proxy.device_id

    def context_menu(self, pos):
        selection_model = self.tree_widget.selectionModel()
        if selection_model is None:
            return

        menu = QMenu(parent=self.widget)
        action_validate = menu.addAction("Validate")
        action_validate.triggered.connect(self.on_validate)
        action_show = menu.addAction("Show Detailed Scene")
        action_show.triggered.connect(self.on_show_scene)
        if self._excluded_devices:
            device_exclude = menu.addAction("Device Selection")
            device_exclude.triggered.connect(self.on_device_exclude)
        menu.exec(self.tree_widget.viewport().mapToGlobal(pos))

    def current_item(self):
        """Return the current selected item of the treewidget"""
        item = None
        index = self.tree_widget.selectionModel().selectedRows()[0]
        if index.isValid():
            index = self.filterModel().mapToSource(index)
            item = self.sourceModel().item(index.row(), 1)

        return item

    def on_show_scene(self):
        item = self.current_item()
        if item is None:
            return

        get_scene_from_server(self.instanceId, "group_detail",
                              groupId=item.text())

    def on_validate(self):
        item = self.current_item()
        if item is None:
            return

        get_scene_from_server(self.instanceId, "group_detail",
                              groupId=item.text(), validate=True)

    def on_device_exclude(self):
        item = self.current_item()
        if item is None:
            return

        groupId = item.text()
        devices, excluded = self.get_group_devices(groupId)
        dialog = SelectionDialog(devices, excluded, parent=self.widget)
        if dialog.exec() == QDialog.Accepted:
            sources = dialog.devices
            call_device_slot(WeakMethodRef(self.on_selection),
                             self.instanceId, "requestAction",
                             action="excludedDevices", groupId=groupId,
                             sources=sources)

    def on_selection(self, success, reply):
        if not success:
            reason, detail = get_reason_parts(reply)
            messagebox.show_error(reason, details=detail)
