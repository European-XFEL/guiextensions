#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from functools import partial

from qtpy.QtWidgets import QMenu
from traits.api import Bool, Instance

from karabogui import messagebox
from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.controllers.table.api import BaseTableController
from karabogui.request import call_device_slot

from .models.simple import DoocsLocationTableModel


def request_handler(mirror_id, action, success, reply):
    """Callback handler for a request to the DOOCS manager"""
    if not success or not reply.get('payload.success', False):
        msg = ("Error: Properties could not be updated. "
               "See the device server log for additional details: "
               f"{reply.get('payload.reason')}")
        messagebox.show_warning(msg, title='Manager Service Failed')
    return


@register_binding_controller(
    ui_name='Doocs Device Table',
    klassname='DoocsTable',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type('DoocsLocationTable'),
    priority=-10, can_show_nothing=True)
class DisplayDoocsLocationTable(BaseTableController):
    """A table version for the DoocsML"""
    model = Instance(DoocsLocationTableModel, args=())
    hasCustomMenu = Bool(True)

    def custom_menu(self, pos):
        """The custom context menu of a reconfigurable table element"""
        index = self.currentIndex()
        if not index.isValid():
            return

        menu = QMenu(parent=self.widget)
        label = self.widget.model().index(index.row(), 0).data()
        menu.addAction(label)
        menu.addSeparator()
        show_properties_action = menu.addAction(
            'Show Available Properties')
        show_properties_action.triggered.connect(
            partial(self._show_properties, label, "requestManagerShowAction"))
        remove_properties_action = menu.addAction(
            'Remove Device')
        remove_properties_action.triggered.connect(
            partial(self._show_properties, label,
                    "requestManagerRemoveAction"))

        menu.exec_(self.widget.viewport().mapToGlobal(pos))

    def _show_properties(self, server, callback_func):
        """Call the manager call back function callback_func to perform some
        action in the device"""
        device_id = self.proxy.root_proxy.device_id
        handler = partial(request_handler, device_id, server)
        call_device_slot(handler, device_id, callback_func, action=server)
