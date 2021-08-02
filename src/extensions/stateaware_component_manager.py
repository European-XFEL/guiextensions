#############################################################################
# Author: <steffen.hauf@xfel.eu>
# Created on May 11, 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections import OrderedDict
from functools import partial

from karabo.common.states import State
from karabo.native import Hash
from karabogui.binding.api import (
    PropertyProxy, WidgetNodeBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.request import call_device_slot, send_property_changes
from karabogui.singletons.api import get_manager, get_network, get_topology
from qtpy.QtCore import QModelIndex, Qt, QTimer
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView, QAction, QHBoxLayout, QHeaderView, QLabel, QSizePolicy,
    QToolBar, QToolButton, QTreeView, QVBoxLayout, QWidget)
from traits.api import Bool, Dict, Instance, List, String, WeakRef

from .models.simple import StateAwareComponentManagerModel

LABEL_MAPPING = OrderedDict()
LABEL_MAPPING["Class"] = "classId"
LABEL_MAPPING["Is State"] = "current_state"
LABEL_MAPPING["Intended State"] = "pre_state"
LABEL_MAPPING["Pre-Config Action"] = "pre_action"
LABEL_MAPPING["Configure State"] = "post_state"
LABEL_MAPPING["Post-Config Action"] = "post_action"
LABEL_MAPPING["Final State"] = "final_state"
LABEL_MAPPING["Do Post-Config Action"] = "do_final_action"
LABEL_MAPPING["Status"] = "status"


TOOL_TIPS = OrderedDict()
TOOL_TIPS["classId"] = "Class Id of the device"
TOOL_TIPS["current_state"] = (
    "The state the device was in, when verify configuration was clicked")
TOOL_TIPS["pre_state"] = (
    "The state the device is expected to be in before component "
    "manager-driven state updates happen")
TOOL_TIPS["pre_action"] = (
    "Action performed on this device to transition from the 'Intended State' "
    "to the 'Configure State'")
TOOL_TIPS["post_state"] = (
    "State in which the new configuration will be applied!")
TOOL_TIPS["post_action"] = (
    "Optional action performed after configuration which transitions the "
    "device into a 'Final State' after configuration.")
TOOL_TIPS["final_state"] = (
    "'Final State' of the device after component manager-driven actions.")
TOOL_TIPS["do_final_action"] = (
    "Check this to perform the 'Final Action' after configuration, i.e. "
    "transition the device to a state other than the 'Configure State'.")
TOOL_TIPS["status"] = (
    "Status of reconfiguration. Details on errors will be shown as tool-tips "
    "on the individual device's status.")


# symbols are ordered by imporants in color resolution
# on the group
STATUS_SYMBOL = OrderedDict()
STATUS_SYMBOL["UNKNOWN"] = "\u25CC", Qt.white
STATUS_SYMBOL["INIT"] = "\u25CB", Qt.white
STATUS_SYMBOL["PENDING"] = "\u2298", Qt.lightGray
STATUS_SYMBOL["DONE"] = "\u25CF", Qt.green
STATUS_SYMBOL["POST"] = "\u25D4", Qt.cyan
STATUS_SYMBOL["FINAL"] = "\u25D5", Qt.blue
STATUS_SYMBOL["ERROR"] = "\u2716", Qt.red


HAS_STATE_TRANSITION_COLOR = Qt.yellow
KEEPS_STATE_COLOR = Qt.green
UNDEFINED_COLOR = Qt.cyan

SELECT_ALL_LABEL = "All"
SELECT_NONE_LABEL = "None"
SELECT_BY_STATE_LABEL = "State not changed"
SELECT_INVERT_LABEL = "Invert"
APPLY_UPDATES_LABEL = "Accept External Updates"
REJECT_UPDATES_LABEL = "Reject External Updates"


NODE_CLASS_NAME = '_StateAwareComponentManager'
_is_compatible = with_display_type('WidgetNode|StateAwareComponentManagerView')


def find_column_index(clabel):
    for i, label in enumerate(LABEL_MAPPING.values()):
        if label == clabel:
            return i
    return None


@register_binding_controller(ui_name='State Aware Component Manager View',
                             can_edit=True,
                             klassname='StateAwareComponentManager',
                             binding_type=WidgetNodeBinding,
                             is_compatible=_is_compatible, priority=90)
class StateAwareComponentManager(BaseBindingController):
    # The scene model class used by this controller
    model = Instance(StateAwareComponentManagerModel, args=())
    # Private traits
    _is_editing = Bool(False)
    _expanded = Bool(False)
    _is_updating = Bool(False)

    _expanded_indexes = List(args=())
    _selected_devices = List(args=())
    _groups = List(args=())
    _external_actions = List(args=())
    _initialized = Bool(False)
    _treeview = WeakRef(QTreeView)
    _item_model = WeakRef(QStandardItemModel)
    _overlay = WeakRef(QLabel)
    _selection_proxy = Instance(PropertyProxy)
    _device_refs = Dict(String, WeakRef(QStandardItem))
    _previous_status = Dict(String, String)
    _timer = Instance(QTimer)

    def create_widget(self, parent):
        widget = QWidget(parent=parent)
        layout = QVBoxLayout(widget)
        header_layout = QHBoxLayout()
        self._treeview = QTreeView(parent=widget)
        self._treeview.setUniformRowHeights(True)
        self._item_model = QStandardItemModel(parent=self._treeview)
        self._item_model.setHorizontalHeaderLabels(LABEL_MAPPING.keys())
        self._item_model.itemChanged.connect(self._item_edited)

        header = self._treeview.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.sectionDoubleClicked.connect(self.onDoubleClickHeader)

        self._treeview.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._treeview.setModel(self._item_model)
        self._treeview.setSizePolicy(QSizePolicy.MinimumExpanding,
                                     QSizePolicy.MinimumExpanding)

        # add filter buttons
        tool_bar = QToolBar("Filter")
        tool_bar.addAction(SELECT_ALL_LABEL)
        tool_bar.addAction(SELECT_NONE_LABEL)
        tool_bar.addAction(SELECT_BY_STATE_LABEL)
        tool_bar.addAction(SELECT_INVERT_LABEL)

        apply_ext = QAction(APPLY_UPDATES_LABEL)
        tool_bar.addAction(apply_ext)
        overwrite_ext = QAction(REJECT_UPDATES_LABEL)
        tool_bar.addAction(overwrite_ext)

        style = ("QWidget { border: 1px solid black; }"
                 "QWidget:hover { background-color: #e8f1ff; }")
        for action in tool_bar.actions():
            tool_bar.widgetForAction(action).setStyleSheet(style)
        self._external_actions = [apply_ext, overwrite_ext]

        tool_bar.actionTriggered[QAction].connect(self.tool_bar_action)

        header_layout.addWidget(tool_bar)

        # an overlay widget
        self._overlay = QLabel(parent=widget)
        style = "QLabel { background-color : white; color : red; border: 1px solid black;}"  # noqa
        self._overlay.setStyleSheet(style)
        header_layout.addWidget(self._overlay)

        layout.addLayout(header_layout)
        layout.addWidget(self._treeview)

        widget.setSizePolicy(QSizePolicy.MinimumExpanding,
                             QSizePolicy.MinimumExpanding)

        root_proxy = self.proxy.root_proxy
        self._selection_proxy = PropertyProxy(root_proxy=root_proxy,
                                              path='selectionList.devices')

        # request status once:
        self._request_status()
        # and setup the timer we trigger when configuration happens
        self._timer = QTimer(parent)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._request_status)

        return widget

    def _update_check_state_all(self, state):
        # update all check boxes to the same state
        for i in range(self._item_model.rowCount(QModelIndex())):
            group = self._item_model.item(i)
            for j in range(group.rowCount()):
                item = group.child(j)
                item.setCheckState(state)

    def tool_bar_action(self, action):

        if action.text() == SELECT_ALL_LABEL:
            self._update_check_state_all(Qt.Checked)
        elif action.text() == SELECT_NONE_LABEL:
            self._update_check_state_all(Qt.Unchecked)
        elif action.text() == SELECT_BY_STATE_LABEL:
            # first deselect all
            self._update_check_state_all(Qt.Unchecked)
            # now select those where the pre state transition is keep
            for i in range(self._item_model.rowCount(QModelIndex())):
                group = self._item_model.item(i)
                pre_state = self._item_model.item(i, 2)
                pre_text = pre_state.text()
                if pre_text == "keep" or pre_text == "undefined":
                    for j in range(group.rowCount()):
                        item = group.child(j)
                        item.setCheckState(Qt.Checked)
        elif action.text() == SELECT_INVERT_LABEL:
            # invert our selection
            for i in range(self._item_model.rowCount(QModelIndex())):
                group = self._item_model.item(i)
                for j in range(group.rowCount()):
                    item = group.child(j)
                    state = item.checkState()
                    item.setCheckState(Qt.Checked if state == Qt.Unchecked
                                       else Qt.Unchecked)

        elif action.text() == APPLY_UPDATES_LABEL:
            # applies updates from the device
            self._initialized = False
            network, manager, topology = (get_network(), get_manager(),
                                          get_topology())

            device_id = self.proxy.root_proxy.device_id
            device_proxy = topology.get_device(device_id)
            manager.expect_properties(device_proxy, [self.proxy])
            network.onGetDeviceConfiguration(device_id)
        elif action.text() == REJECT_UPDATES_LABEL:
            # overwrites the device value with ours
            self._initialized = True
            self._selection_proxy.edit_value = self._build_value()
            send_property_changes([self._selection_proxy])

    def on_device_list(self, group_item, remote, fin_action,
                       fin_action_select, success, reply):
        """
        Call-back for when device list is received.
        """
        if not success:
            return
        payload = reply.get("payload")
        entry = payload.get("entry", None)
        node = payload.get("node", "")
        if not entry:
            return

        devices = entry.get("devices", None)
        if not devices:
            return

        self._treeview.setUpdatesEnabled(False)
        self._is_updating = True

        row, column = 0, 0

        for device in devices:
            device_item = QStandardItem(device["deviceId"])
            device_item.setEditable(False)
            device_item.setCheckable(True)
            if device["deviceId"] in self._selected_devices:
                if device_item.checkState() != Qt.Checked:
                    device_item.setCheckState(Qt.Checked)
            group_item.setChild(row, column, device_item)
            column += 1

            # on expansion we retreive the changes
            btn_item = QStandardItem(f"{device['changes']} changes")
            btn_item.setEditable(False)
            btn_diff = QToolButton()
            btn_diff.setText(f"View {device['changes']} changes")

            def request_diff(item=None, btn=None, device=device):
                call_device_slot(partial(self.on_diff, item, btn),
                                 remote, "requestDeviceDiff",
                                 node=node, device=device["deviceId"])

            # diffs are requested in a lazy fashion
            btn_diff.clicked.connect(partial(request_diff, item=device_item,
                                             btn=btn_diff, device=device))
            group_item.setChild(row, column, btn_item)
            self._treeview.setIndexWidget(btn_item.index(), btn_diff)

            do_final_action_itm = QStandardItem("")  # no text on this item
            do_final_action_itm.setCheckable(True)
            do_final_action_itm.setCheckState(fin_action)
            do_final_action_itm.setEnabled(fin_action_select)
            group_item.setChild(row, find_column_index("do_final_action"),
                                do_final_action_itm)

            status_item = QStandardItem(STATUS_SYMBOL["UNKNOWN"][0])
            group_item.setChild(row, find_column_index("status"),
                                status_item)

            # add to the references
            self._device_refs[device["deviceId"]] = status_item
            row, column = row + 1, 0

        # since we reapplied check marks as part of the update
        # re-evaluate the tri-states here. Only children could have been
        # changed, so we do not look at the top-level items.
        self._evaluate_tristates(False, which="device")
        self._is_updating = False
        self._treeview.setUpdatesEnabled(True)

    def on_diff(self, device_item, btn, success, reply):
        """
        Callback for a diff request for a device
        """
        if not success:
            return

        payload = reply.get("payload", None)
        if not payload:
            return

        diff = payload.get("diff", None)
        if not diff:
            return

        row, column = 0, 0
        for path in diff.paths():
            if isinstance(diff[path], Hash):
                continue
            cols = [path, diff[path][0], diff[path][1]]

            for vv in cols:
                add_item = QStandardItem(str(vv))
                add_item.setEditable(False)
                device_item.setChild(row, column, add_item)
                column += 1
            row, column = row + 1, 0

        self._treeview.setExpanded(device_item.index(), True)
        btn.setEnabled(False)

    def _request_status(self):
        prev_status = Hash()
        for k, v in self._previous_status.items():
            prev_status[k] = v

        remote = self.proxy.root_proxy.device_id
        call_device_slot(self.on_status, remote, "requestDeviceStatus",
                         previousStatus=prev_status)

    def on_status(self, success, reply):
        """
        Callback for a status request
        """
        if not success:
            return

        payload = reply.get("payload", None)
        if not payload:
            return

        status = payload.get("status", None)
        if not status:
            return

        new_status = {}

        for deviceId, entry, _ in status.iterall():
            new_status[deviceId] = entry
            sitem = self._device_refs.get(deviceId, None)
            if sitem:
                # nothing to do for init except update the status
                symbol = None
                color = None
                context = None
                if entry == "INIT":
                    symbol, color = (STATUS_SYMBOL["INIT"])
                else:
                    typ, detail = entry.split(":", 1)
                    if typ == "OK":
                        symb = STATUS_SYMBOL.get(detail.upper(), ("?", "red"))
                        symbol, color = symb
                    elif typ == "ERR":
                        symbol, color = STATUS_SYMBOL["ERROR"]
                        context = detail
                    elif typ == "DONE":
                        symbol, color = STATUS_SYMBOL["DONE"]
                        symbol += f" {detail}"  # is a state
                    elif typ == "FAILED":
                        symbol, color = STATUS_SYMBOL["ERROR"]
                        state, context = detail.split(":", 1)
                        context = context.split("exception=")[-1]
                        symbol += f" {state}"

                if symbol:
                    sitem.setText(symbol)
                    sitem.setBackground(color)
                    if context is not None:
                        sitem.setToolTip(context)
                    else:
                        sitem.setToolTip("status")

        # now sort out the group status
        col = find_column_index("status")
        for i in range(self._item_model.rowCount(QModelIndex())):
            group = self._item_model.item(i)
            set_group = self._item_model.item(i, col)
            # we go by color
            colors = []
            for j in range(group.rowCount()):
                item = group.child(j, col)
                colors.append(item.background())
            group_color = None
            for _, color in reversed(STATUS_SYMBOL.values()):
                if color in colors:
                    group_color = color
                    break
            if group_color:
                set_group.setBackground(group_color)

        # resize that status field is large enough
        self._treeview.resizeColumnToContents(col)

        # we keep track of status request so we only update changes
        self._previous_status = new_status

    def _toggle_checkboxes_editable(self, toggle):
        for i in range(self._item_model.rowCount(QModelIndex())):
            group = self._item_model.item(i)
            fa_col = find_column_index("do_final_action")
            final_action_group = self._item_model.item(i, fa_col)

            # items without a config action stay disabled
            pitem = self._item_model.item(i,
                                          find_column_index("post_action"))
            ftoggle = toggle and pitem.text() != "undefined"

            group.setEnabled(toggle)
            final_action_group.setEnabled(ftoggle)
            for j in range(group.rowCount()):
                ditem = group.child(j)
                if ditem:
                    ditem.setEnabled(toggle)

                fitem = group.child(j, find_column_index("do_final_action"))
                if fitem and pitem:
                    fitem.setEnabled(ftoggle)

    def state_update(self, proxy):
        updated_dev = proxy.root_proxy
        value = get_binding_value(updated_dev.state_binding, '')
        if value == '':
            return
        state = State(value)
        if state != State.ENGAGED:
            self._is_updating = True
            self._toggle_checkboxes_editable(False)
            msg = ("Changes are being or have been applied! "
                   "Verify configurations to apply a new configuration!")
            self._toggle_overlay(True, msg)

        else:
            self._is_updating = False
            self._toggle_checkboxes_editable(True)
            self._toggle_overlay(False)

        if state == State.CHANGING:
            self._timer.start()
        else:
            self._timer.stop()
        # request once to catch any updates outside the timer
        self._request_status()

    def _toggle_overlay(self, show, msg=None):
        if show:
            self._overlay.setText(f"\U0001F512 {msg}")
        else:
            self._overlay.setText("\U0001F511")

    def value_update(self, proxy):
        # Avoid messing with the item model when the user checks an item
        if self._is_editing:
            return

        tv = self._treeview
        # if values have not changed we do not do anything
        val = get_binding_value(proxy, None)
        if val is None and get_binding_value(val.devices, None) is None:
            return

        selected_devices = get_binding_value(val.devices, [])
        groups = get_binding_value(val.groups, [])

        dev_equal = set(selected_devices) == set(self._selected_devices)
        grp_equal = set(groups) == set(self._groups)

        # if only the device selection changes we do not update
        # unless forced
        if self._initialized and grp_equal:
            if not dev_equal:
                tv.setEnabled(False)
                # enable external actions
                for act in self._external_actions:
                    act.setEnabled(True)
                msg = "Please accept or reject external updates!"
                self._toggle_overlay(True, msg)
            else:
                tv.setEnabled(True)
                for act in self._external_actions:
                    act.setEnabled(False)
                self._toggle_overlay(False)
            return

        self._toggle_overlay(False)
        tv.setEnabled(True)
        for act in self._external_actions:
            act.setEnabled(False)

        self._initialized = True
        self._is_updating = True

        # We reset on every value update!
        self._expanded = False

        def _build(node, parent_item):
            group_items = []
            behaviour = "ChangeState"
            do_final_action = Qt.Unchecked
            allow_final_action_select = True
            # groups contain all the high-level information encoded in
            # their name
            comps = node.split(":")
            post_config_action = True
            for i, comp in enumerate(comps):
                item = QStandardItem(comp)
                # track if we are keeping state the same in this group
                if comp == "keep":
                    behaviour = "KeepState"
                elif comp == "undefined":
                    behaviour = "Undefined"
                    if i == find_column_index("post_action"):
                        post_config_action = False
                if i == 0 or i == find_column_index("do_final_action"):
                    item.setCheckable(True)
                    if i == find_column_index("do_final_action"):
                        item.setText("")  # no text on this item
                        if comp == "True":
                            checked = Qt.Checked
                            do_final_action = Qt.Checked
                        else:
                            checked = Qt.Unchecked
                        item.setCheckState(checked)
                        # if there is no post-config action defined
                        # we lock this to false
                        if not post_config_action:
                            item.setEnabled(False)
                            allow_final_action_select = False

                # users should not edit text in the table view
                item.setEditable(False)

                group_items.append(item)
            # append the status column
            item = QStandardItem("")
            group_items.append(item)
            self._device_refs[node] = item
            # set colors depending on whether a State change will happen
            for item in group_items:
                if behaviour == "KeepState":
                    item.setBackground(KEEPS_STATE_COLOR)
                elif behaviour == "ChangeState":
                    item.setBackground(HAS_STATE_TRANSITION_COLOR)
                else:
                    item.setBackground(UNDEFINED_COLOR)
            parent_item.appendRow(group_items)

            remote_device = proxy.root_proxy.device_id

            # lazyly ask for the devices for each group
            call_device_slot(partial(self.on_device_list,
                                     group_items[0], remote_device,
                                     do_final_action,
                                     allow_final_action_select),
                             remote_device,
                             "requestNodeDevices",
                             node=node)

        tv.setUpdatesEnabled(False)

        # Since we are about to reset our model, we store the expanded state
        # of the widget for comfort
        self.save_expanded()
        # Clear self._item_model before updating
        self._item_model.clear()
        self._item_model.setHorizontalHeaderLabels(LABEL_MAPPING.keys())

        # add header tooltips
        for i, hid in enumerate(LABEL_MAPPING.values()):
            hitem = self._item_model.horizontalHeaderItem(i)
            hitem.setToolTip(TOOL_TIPS.get(hid, hid))

        root_item = self._item_model.invisibleRootItem()

        if val:
            if groups:
                for entry in groups:
                    _build(entry, root_item)

            # save current check state for when we get the dvive lists in
            self._selected_devices = selected_devices
            self._groups = groups

        # Finally, we safely restore the expanded index by displayed name
        self.restore_expanded()
        tv.setUpdatesEnabled(True)
        self._is_updating = False

    def save_expanded(self):
        self._expanded_indexes = []
        tv = self._treeview
        model = self._item_model

        for row in range(model.rowCount()):
            index = model.index(row, 0)
            index_data = index.data(role=Qt.DisplayRole)
            if index_data is not None and tv.isExpanded(index):
                self._expanded_indexes.append(index_data)

    def restore_expanded(self):
        tv = self._treeview
        model = tv.model()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            index_data = index.data(role=Qt.DisplayRole)
            if index_data is not None and index_data in self._expanded_indexes:
                tv.setExpanded(index, True)
        self._expanded_indexes = []

    def _item_edited(self, item):
        if self.proxy.binding is None:
            return

        if self._is_updating:
            return

        # status updates are ignored:
        if item in self._device_refs.values():
            return

        try:
            self._is_editing = True
            self._is_updating = True
            is_toplevel = item.parent() is None
            if item.column() == 0:
                self._evaluate_tristates(is_toplevel, which="device")
            else:
                self._evaluate_tristates(is_toplevel, which="do_final")
            self._selection_proxy.edit_value = self._build_value()
            send_property_changes([self._selection_proxy])

        finally:
            self._is_editing = False
            self._is_updating = False

    def onDoubleClickHeader(self):
        if self._expanded:
            self._treeview.collapseAll()
        else:
            self._treeview.expandAll()

        self._expanded = not self._expanded

    def _evaluate_tristates(self, is_toplevel, which="device"):
        """
        Evaluates the tri-state level along the hierarchy.

        :param is_toplevel: set to true if top-level elements are changed
        """
        # we need the checked devices, not the checked groups
        # so we go to the second tree level
        for i in range(self._item_model.rowCount(QModelIndex())):
            group = self._item_model.item(i)
            if which == "device":
                set_group = group
                col = 0
            else:
                col = find_column_index("do_final_action")
                set_group = self._item_model.item(i, col)

            # if its a top-level change we evaluate all children, but
            # leave the group untouched
            if is_toplevel:
                for j in range(group.rowCount()):
                    item = group.child(j, col)
                    item.setCheckState(set_group.checkState())
            else:
                # we set the group check-state to the child check-states
                checked = []
                for j in range(group.rowCount()):
                    item = group.child(j, col)
                    checked.append(item.checkState() == Qt.Checked)
                if all(checked):
                    set_group.setCheckState(Qt.Checked)
                elif any(checked):
                    set_group.setCheckState(Qt.PartiallyChecked)
                else:
                    set_group.setCheckState(Qt.Unchecked)

    def _build_value(self):
        """
        Build the return value to set to the selectionList.devices field

        :return: a list of devices which are selected
        """
        devices = []
        # we need the checked devices, not the checked groups
        # so we go to the second tree level
        for i in range(self._item_model.rowCount(QModelIndex())):
            group = self._item_model.item(i)
            for j in range(group.rowCount()):
                item = group.child(j)
                if item.checkState() == Qt.Checked:
                    # check if a final state change is requested
                    fitem = group.child(j,
                                        find_column_index("do_final_action"))
                    do_final_action = fitem.checkState() == Qt.Checked
                    devices.append(f"{item.text()}:{do_final_action}")
        self._selected_devices = devices
        return devices
