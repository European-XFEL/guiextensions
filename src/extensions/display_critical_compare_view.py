#############################################################################
# Author_layout: <dennis.goeries@xfel.eu>
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from functools import partial

from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtWidgets import (
    QHBoxLayout, QLayout, QLineEdit, QMenu, QPushButton, QVBoxLayout, QWidget)
from traits.api import Bool, Instance

from extensions.dialogs.api import CompareDialog
from karabogui import messagebox
from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.controllers.table.api import BaseTableController
from karabogui.request import call_device_slot
from karabogui.util import WeakMethodRef

from .models.api import CriticalCompareViewModel


@register_binding_controller(
    ui_name="Critical Compare View",
    klassname="CriticalCompareView",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("CriticalCompareView"),
    priority=-10, can_show_nothing=False)
class DisplayCriticalCompareView(BaseTableController):
    model = Instance(CriticalCompareViewModel, args=())

    searchLabel = Instance(QLineEdit)
    hasCustomMenu = Bool(True)

    def create_widget(self, parent):
        table_widget = super().create_widget(parent)
        widget = QWidget(parent)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSizeConstraint(QLayout.SetNoConstraint)

        hor_layout = QHBoxLayout()
        hor_layout.setContentsMargins(0, 0, 0, 0)
        hor_layout.setSizeConstraint(QLayout.SetNoConstraint)

        self.searchLabel = QLineEdit(widget)
        clear_button = QPushButton("Clear", parent=widget)
        clear_button.clicked.connect(self.searchLabel.clear)
        hor_layout.addWidget(self.searchLabel)
        hor_layout.addWidget(clear_button)

        # Complete widget layout and return widget
        widget_layout.addLayout(hor_layout)
        widget_layout.addWidget(table_widget)
        widget.setLayout(widget_layout)

        return widget

    def createModel(self, model):
        """Create the filter model for the table"""
        filter_model = QSortFilterProxyModel()
        filter_model.setSourceModel(model)
        filter_model.setFilterRole(Qt.DisplayRole)
        filter_model.setFilterKeyColumn(0)
        filter_model.setFilterCaseSensitivity(False)
        filter_model.setFilterFixedString("")
        self.searchLabel.textChanged.connect(filter_model.setFilterFixedString)
        return filter_model

    def getModelData(self, row, column, role=Qt.DisplayRole):
        return self.sourceModel().index(row, column).data(role=role)

    def getInstanceId(self):
        return self.proxy.root_proxy.device_id

    def custom_menu(self, pos):
        index = self.currentIndex()
        if not index.isValid():
            return

        menu = QMenu(parent=self.widget)
        action_show_changes = menu.addAction("Show Changes")
        action_show_changes.triggered.connect(self.onViewChanges)
        menu.exec(self.tableWidget().viewport().mapToGlobal(pos))

    def request_handler(self, device_id, success, reply):
        if not success:
            messagebox.show_error(f"Request for {device_id} timed out.")
            return

        payload = reply["payload"]
        if not payload["success"]:
            reason = payload["reason"]
            messagebox.show_error(f"Request for {device_id} not "
                                  f"successful: {reason}.")
            return

        data = payload["data"]
        dialog = CompareDialog(title="Critical Comparison View",
                               data=data)
        dialog.exec()

    def onViewChanges(self):
        index = self.currentIndex()
        if not index.isValid():
            return

        device_id = self.getModelData(index.row(), 0)
        handler = partial(WeakMethodRef(self.request_handler), device_id)
        call_device_slot(handler, self.getInstanceId(),
                         "requestAction", action="view", deviceId=device_id)
