#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on April 15, 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from contextlib import contextmanager

from qtpy.QtCore import Qt
from qtpy.QtGui import QPalette, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QMenu, QSizePolicy,
    QStackedWidget, QTextEdit, QTreeView, QWidget)
from traits.api import Bool, Instance, WeakRef

from extensions.icons import runfile
from karabo.common.api import WeakMethodRef
from karabo.native import create_html_hash
from karabogui.api import (
    BaseBindingController, VectorHashBinding, VectorUint64Binding,
    call_device_slot, get_binding_value, get_reason_parts, get_spin_widget,
    icons, messagebox, register_binding_controller, with_display_type)

from ..models.api import DisplayRunMonitorHistoryModel

UPDATE_NEW_PROPOSAL = 1
UPDATE_NEW_RUN = 2
BLANK_PAGE = 0
WAITING_PAGE = 1
INFO_PAGE = 2

OVERVIEW_DISPLAY_TYPE = "RunMonitor|History"
UPDATE_DISPLAY_TYPE = "RunMonitor|UpdateHistory"
HEADER_LABELS = ["File Explorer"]


class InfoWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)


class ProposalItem(QStandardItem):
    def __init__(self, value: int):
        super().__init__(icons.folder, str(value))
        self.setEditable(False)
        self.setData([], Qt.UserRole)


class RunDataItem(QStandardItem):
    def __init__(self, run: int, proposal: int):
        super().__init__(runfile.icon, f"{run:04}")
        self.setData({"run": run, "proposal": proposal}, Qt.UserRole)


@contextmanager
def setUpdatedDisabled(view: QTreeView):
    """Transiently disable updates for a QTreeView instance"""
    view.setUpdatesEnabled(False)
    yield
    view.setUpdatesEnabled(True)


@register_binding_controller(
    ui_name="RunMonitor History",
    klassname="RunMonitorHistory",
    binding_type=(VectorHashBinding, VectorUint64Binding),
    is_compatible=with_display_type(OVERVIEW_DISPLAY_TYPE),
    can_edit=False, priority=40, can_show_nothing=False)
class RunMonitorHistory(BaseBindingController):
    model = Instance(DisplayRunMonitorHistoryModel, args=())

    tree_view = WeakRef(QTreeView)
    stacked_widget = WeakRef(QStackedWidget)
    info_widget = WeakRef(QTextEdit)
    item_model = WeakRef(QStandardItemModel)

    _expanded = Bool(False)

    def create_widget(self, parent):
        widget = QWidget(parent)
        tree_view = QTreeView(parent=parent)
        tree_view.setMaximumWidth(200)
        tree_view.setFocusPolicy(Qt.StrongFocus)
        tree_view.setUniformRowHeights(True)
        tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        tree_view.customContextMenuRequested.connect(self.context_menu)
        tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree_view = tree_view

        header = tree_view.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.sectionDoubleClicked.connect(self.onDoubleClickHeader)

        item_model = QStandardItemModel(parent=widget)
        item_model.setHorizontalHeaderLabels(HEADER_LABELS)
        self.item_model = item_model
        self.tree_view.setModel(item_model)

        # Stacked widget parameters
        self.stacked_widget = QStackedWidget(widget)
        self.stacked_widget.addWidget(InfoWidget(widget))

        wait_widget = get_spin_widget(icon="wait", parent=widget)
        wait_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        wait_widget.setAutoFillBackground(True)
        wait_widget.setBackgroundRole(QPalette.Base)
        self.stacked_widget.addWidget(wait_widget)

        self.info_widget = InfoWidget(widget)
        self.stacked_widget.addWidget(self.info_widget)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tree_view)
        layout.addWidget(self.stacked_widget)
        widget.setSizePolicy(QSizePolicy.MinimumExpanding,
                             QSizePolicy.MinimumExpanding)
        widget.setFocusProxy(tree_view)

        self.tree_view.selectionModel().selectionChanged.connect(
            self.onGetRunInfo)
        return widget

    def add_proxy(self, proxy):
        if proxy.binding is None:
            return True

        if proxy.binding.display_type == UPDATE_DISPLAY_TYPE:
            return True

        return False

    def value_update(self, proxy):
        if proxy is self.proxy:
            if self.item_model.rowCount():
                return

            def create_proposal(row_hash, root_item):
                proposal = row_hash["proposal"]
                proposal_item = ProposalItem(proposal)
                runs_list = []
                for run in row_hash["runs"]:
                    runs_list.append(run)
                    proposal_item.appendRow(
                        [RunDataItem(run, proposal)])

                proposal_item.setData(runs_list, Qt.UserRole)
                root_item.appendRow([proposal_item])

            with setUpdatedDisabled(self.tree_view):
                root_item = self.rootItem
                for row in get_binding_value(proxy, []):
                    create_proposal(row, root_item)

        else:
            value = get_binding_value(proxy.binding, [])
            if not len(value):
                return
            update_type = value[0]
            if update_type == UPDATE_NEW_RUN:
                proposal = value[1]
                proposal_item = self.find_proposal(proposal)
                if proposal_item is not None:
                    run = value[2]
                    runs_list = proposal_item.data(Qt.UserRole)
                    if run in runs_list:
                        return
                    runs_list.append(run)
                    run_item = RunDataItem(run, proposal)
                    proposal_item.appendRow([run_item])
                    proposal_item.setData(runs_list, Qt.UserRole)
            elif update_type == UPDATE_NEW_PROPOSAL:
                proposal = value[1]
                proposal_item = self.find_proposal(proposal)
                if proposal_item is not None:
                    return
                proposal_item = ProposalItem(proposal)
                self.rootItem.appendRow([proposal_item])

    def clear_widget(self):
        """Clear the widget when the instance goes offline"""
        with setUpdatedDisabled(self.tree_view):
            model = self.item_model
            model.removeRows(0, model.rowCount())
            self.set_stack_index(BLANK_PAGE)

    # ----------------------------------------------------------------------

    def set_stack_index(self, index):
        self.stacked_widget.blockSignals(True)
        self.stacked_widget.setCurrentIndex(index)
        self.stacked_widget.blockSignals(False)

    def find_proposal(self, proposal: int):
        items = self.item_model.findItems(str(proposal))
        return items[0] if len(items) else None

    @property
    def rootItem(self):
        return self.item_model.invisibleRootItem()

    # Action Interface
    # ----------------------------------------------------------------------

    @property
    def instanceId(self):
        return self.proxy.root_proxy.device_id

    def context_menu(self, pos):
        data = self.selected_data()
        if data is None:
            return

        menu = QMenu(parent=self.widget)
        action_run_history = menu.addAction("Show Info")
        action_run_history.triggered.connect(self.onGetRunInfo)
        menu.exec(self.tree_view.viewport().mapToGlobal(pos))

    def selected_data(self):
        """Return the current selected item of the treewidget"""
        selection_model = self.tree_view.selectionModel()
        if not selection_model.hasSelection():
            return
        index = selection_model.selectedIndexes()[0]
        item = self.item_model.itemFromIndex(index)
        if isinstance(item, ProposalItem):
            return
        return index.data(Qt.UserRole)

    # Slots
    # ----------------------------------------------------------------------

    def onDoubleClickHeader(self):
        if self._expanded:
            self.tree_view.collapseAll()
        else:
            self.tree_view.expandAll()
        self._expanded = not self._expanded

    def onGetRunInfo(self):
        data = self.selected_data()
        if data is None:
            self.set_stack_index(BLANK_PAGE)
            return

        self.set_stack_index(WAITING_PAGE)
        call_device_slot(WeakMethodRef(self.onRetrieveRun),
                         self.instanceId, "requestAction",
                         proposal=data["proposal"], run=data["run"],
                         action="retrieveRun")

    def onRetrieveRun(self, success, reply):
        if not success:
            self.set_stack_index(BLANK_PAGE)
            reason, details = get_reason_parts(reply)
            messagebox.show_error(reason, details=details)
            return

        self.info_widget.setHtml(create_html_hash(reply))
        self.set_stack_index(INFO_PAGE)
