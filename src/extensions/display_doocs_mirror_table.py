#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from traits.api import Instance

from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    with_display_type, register_binding_controller)
from karabogui.controllers.table.api import (
    BaseTableController, TableButtonDelegate)
from karabogui.request import get_scene_from_server

from .models.simple import DoocsMirrorTableModel

MIRROR_SCENELINK_COLUMN = 2


class ButtonDelegate(TableButtonDelegate):

    def get_button_text(self, index):
        """Reimplemented function of `TableButtonDelegate`"""
        text = "Scene Link"
        return text

    def click_action(self, index):
        """Reimplemented function of `TableButtonDelegate`"""
        if not index.isValid():
            return
        device_id = index.model().index(index.row(), 0).data()
        scene_id = index.model().index(index.row(), 2).data()
        if scene_id is not None:
            get_scene_from_server(device_id, scene_id)


@register_binding_controller(
    ui_name='Doocs Device Table',
    klassname='DoocsMirrorTable',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type('DoocsMirrorTable'),
    priority=-10, can_show_nothing=False)
class DisplayDoocsMirrorTable(BaseTableController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DoocsMirrorTableModel, args=())

    def create_widget(self, parent):

        # get the QTableView
        widget = super(DisplayDoocsMirrorTable, self).create_widget(parent)

        # NOTE: In the future we need to add the widgets for filtering
        return widget

    def create_delegates(self):
        """Create all the table delegates in the table element"""
        bindings = self.getBindings()
        keys = bindings.keys()
        # If we are readOnly, we erase all edit delegates
        for column, key in enumerate(keys):
            self.widget.setItemDelegateForColumn(column, None)
        button_delegate = ButtonDelegate()
        self.widget.setItemDelegateForColumn(MIRROR_SCENELINK_COLUMN,
                                             button_delegate)
