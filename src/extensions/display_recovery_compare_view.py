#############################################################################
# Author_layout: <dennis.goeries@xfel.eu>
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from functools import partial

from qtpy.QtCore import QEvent, QObject
from qtpy.QtWidgets import QMenu
from traits.api import Bool, Instance

from extensions.dialogs.api import CompareDialog
from karabogui import messagebox
from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.controllers.table.api import BaseFilterTableController
from karabogui.request import call_device_slot

try:
    from karabogui.util import WeakMethodRef
except ImportError:
    from karabo.common.api import WeakMethodRef

from .models.api import CriticalCompareViewModel

COLUMN_DEVICE_ID = 0
COLUMN_CLASS_ID = 1


@register_binding_controller(
    ui_name="Critical Compare View",
    klassname="CriticalCompareView",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("CriticalCompareView"),
    priority=-10, can_show_nothing=False)
class DisplayRecoveryCompareView(BaseFilterTableController):
    model = Instance(CriticalCompareViewModel, args=())

    hasCustomMenu = Bool(True)
    eventFilter = Instance(QObject)

    def create_widget(self, parent):
        widget = super().create_widget(parent)

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
        self.tableWidget().viewport().installEventFilter(self.eventFilter)
        return widget

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

        model = index.model()
        _, device_id = model.get_model_data(index.row(), COLUMN_DEVICE_ID)
        handler = partial(WeakMethodRef(self._compare_handler), device_id)
        call_device_slot(handler, self.getInstanceId(),
                         "requestAction", action="view", deviceId=device_id)

    def onViewProperties(self):
        index = self.currentIndex()
        if not index.isValid():
            return

        model = index.model()
        _, classId = model.get_model_data(index.row(), COLUMN_CLASS_ID)
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
        # If we retrieve an empty Hash, all static reconfigurable properties
        # have been compared
        if not len(data):
            text = ("All static reconfigurable properties were considered for"
                    f" comparison of devices of class <b>{classId}</b>!")
        else:
            data = sorted(data)
            props = "".join(f"<li>{prop}</li>" for prop in data)
            text = ("<strong>The following properties were considered: "
                    f"</strong><ul>{props}</ul>")

        messagebox.show_information(text, title="Comparison - Properties",
                                    parent=self.widget)
