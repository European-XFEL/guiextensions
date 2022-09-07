#############################################################################
# Author_layout: <dennis.goeries@xfel.eu>
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from functools import partial

from qtpy.QtCore import QEvent, QObject, QSortFilterProxyModel, Qt
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

try:
    from karabogui.util import WeakMethodRef
except ImportError:
    from karabo.common.api import WeakMethodRef

from .models.api import CriticalCompareViewModel


@register_binding_controller(
    ui_name="Critical Compare View",
    klassname="CriticalCompareView",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("CriticalCompareView"),
    priority=-10, can_show_nothing=False)
class DisplayRecoveryCompareView(BaseTableController):
    model = Instance(CriticalCompareViewModel, args=())

    searchLabel = Instance(QLineEdit)
    hasCustomMenu = Bool(True)
    eventFilter = Instance(QObject)

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

        class EventFilter(QObject):
            def __init__(self, controller):
                super().__init__()
                self.controller = controller

            def eventFilter(self, obj, event):
                if event.type() == QEvent.MouseButtonDblClick:
                    self.controller.onViewChanges()
                    return True
                return super().eventFilter(obj, event)

        self.eventFilter = EventFilter(self)
        table_widget.viewport().installEventFilter(self.eventFilter)
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
        action_show_changes = menu.addAction("Show Compared Properties")
        action_show_changes.triggered.connect(self.onViewProperties)

        menu.exec(self.tableWidget().viewport().mapToGlobal(pos))

    # Action Slots
    # ----------------------------------------------------------------------

    def onViewChanges(self):
        index = self.currentIndex()
        if not index.isValid():
            return

        device_id = self.getModelData(index.row(), 0)
        handler = partial(WeakMethodRef(self._compare_handler), device_id)
        call_device_slot(handler, self.getInstanceId(),
                         "requestAction", action="view", deviceId=device_id)

    def onViewProperties(self):
        index = self.currentIndex()
        if not index.isValid():
            return

        classId = self.getModelData(index.row(), 1)
        handler = partial(WeakMethodRef(self._show_class_handler), classId)
        call_device_slot(handler, self.getInstanceId(),
                         "requestAction", action="compareProperties",
                         classId=classId)

    # Action handlers
    # ----------------------------------------------------------------------

    def _compare_handler(self, device_id, success, reply):
        if not success:
            messagebox.show_error(
                f"Compare request for {device_id} failed.",
                parent=self.widget)
            return

        payload = reply["payload"]
        data = payload["data"]
        dialog = CompareDialog(title="Critical Comparison View",
                               data=data, parent=self.widget)
        dialog.show()

    def _show_class_handler(self, classId, success, reply):
        if not success:
            messagebox.show_error(
                f"Show properties request for {classId} failed.",
                parent=self.widget)
            return

        payload = reply["payload"]
        data = payload["data"]
        # If we retrieve an empty Hash, all properties have been compared
        if not len(data):
            text = ("All properties were considered for comparison of devices "
                    f"of class <b>{classId}</b>!")
        else:
            data = sorted(data)
            props = "".join(f"<li>{prop}</li>" for prop in data)
            text = ("<strong>The following properties were considered: "
                    f"</strong><ul>{props}</ul>")

        messagebox.show_information(text, title="Comparison - Properties",
                                    parent=self.widget)
