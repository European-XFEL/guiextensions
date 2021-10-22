#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on January 24, 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from qtpy.QtCore import QDateTime, Qt
from qtpy.QtWidgets import QAction, QDateTimeEdit, QInputDialog
from traits.api import Instance

from karabogui.binding.api import (
    StringBinding, get_binding_value, get_editor_value)
from karabogui.controllers.api import (
    BaseBindingController, is_proxy_allowed, register_binding_controller,
    with_display_type)
from karabogui.util import SignalBlocker

from .models.simple import EditableDateTimeModel


@register_binding_controller(
    ui_name="Datetime Edit",
    klassname="EditableDateTime",
    binding_type=StringBinding,
    can_edit=True,
    is_compatible=with_display_type("Datetime"),
    priority=90, can_show_nothing=False)
class EditableDateTime(BaseBindingController):
    """The Editable DateTime widget

    It provides the editable input line for date and time as
    well as popup calendar.
    """
    model = Instance(EditableDateTimeModel, args=())

    def create_widget(self, parent):
        widget = QDateTimeEdit(parent)
        widget.dateTimeChanged.connect(self._on_user_edit)
        widget.setCalendarPopup(True)

        widget.setDisplayFormat(self.model.time_format)
        action = QAction("Change datetime format...", widget)
        action.triggered.connect(self._change_time_format)
        widget.addAction(action)

        return widget

    def value_update(self, proxy):
        value = get_editor_value(proxy)
        if value is None:
            return

        date_time = QDateTime.fromString(value, Qt.ISODate)
        if not date_time.toString():
            # Invalid datetime
            return

        with SignalBlocker(self.widget):
            self.widget.setDateTime(date_time)

    def _on_user_edit(self, datetime):
        if self.proxy.binding is None:
            return
        self.proxy.edit_value = datetime.toString(Qt.ISODate)

    def _change_time_format(self):
        text, ok = QInputDialog.getText(
            self.widget, "Enter datetime format", "datetime format = ",
            text=self.model.time_format)
        if not ok:
            return

        self.model.time_format = text
        self.widget.setDisplayFormat(text)
        if get_binding_value(self.proxy) is not None:
            self.value_update(self.proxy)

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)
