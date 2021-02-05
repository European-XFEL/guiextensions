#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from PyQt5.QtWidgets import QTableView
from traits.api import Instance, Undefined

from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    with_display_type, BaseBindingController, register_binding_controller)

from .models.simple import DoocsTableModel


@register_binding_controller(
    ui_name='Doocs Device Table',
    klassname='DoocsTable',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type('DoocsTable'),
    priority=-10, can_show_nothing=False)
class DisplayDoocsTable(BaseBindingController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DoocsTableModel, args=())

    def create_widget(self, parent):
        widget = QTableView(parent=parent)
        return widget

    # ----------------------------------------------------------------

    def binding_update(self, proxy):
        """This method is executed with a schema update of the device"""
        binding = proxy.binding
        attributes = binding.attributes

    def value_update(self, proxy):
        """This method is executed with a value update of the table"""
        value = proxy.value

