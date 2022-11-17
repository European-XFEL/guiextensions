#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from traits.api import Instance

from karabogui.api import (
    BaseFilterTableController, TableButtonDelegate, VectorHashBinding,
    register_binding_controller, with_display_type)
from karabogui.request import get_scene_from_server

from .models.api import DoocsMirrorTableModel
from .utils import requires_gui_version

requires_gui_version(2, 14)

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

        model = index.model()
        _, device_id = model.get_model_data(index.row(), 0)
        _, scene_id = model.get_model_data(index.row(), 2)
        if scene_id is not None:
            get_scene_from_server(device_id, scene_id)


@register_binding_controller(
    ui_name="Doocs Device Table",
    klassname="DoocsMirrorTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("DoocsMirrorTable"),
    priority=-10, can_show_nothing=False)
class DisplayDoocsMirrorTable(BaseFilterTableController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DoocsMirrorTableModel, args=())

    def create_delegates(self):
        """Create all the table delegates in the table element"""
        bindings = self.getBindings()
        # If we are readOnly, we erase all edit delegates
        for column in range(len(bindings)):
            self.tableWidget().setItemDelegateForColumn(column, None)
        button_delegate = ButtonDelegate()
        self.tableWidget().setItemDelegateForColumn(MIRROR_SCENELINK_COLUMN,
                                                    button_delegate)
