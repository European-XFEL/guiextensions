#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from traits.api import Instance

from karabogui import messagebox
from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.controllers.table.api import (
    BaseFilterTableController, TableButtonDelegate)
from karabogui.events import KaraboEvent, broadcast_event
from karabogui.singletons.api import get_network

from .models.api import RecoveryReportTableModel

LOAD_CONFIG_COLUMN = 7


class ButtonDelegate(TableButtonDelegate):

    def get_button_text(self, index):
        """Reimplemented function of `TableButtonDelegate`"""
        text = "Edit"
        return text

    def click_action(self, index):
        """Reimplemented function of `TableButtonDelegate`"""
        if not index.isValid():
            return

        device_id = index.model().index(index.row(), 0).data()
        config_source = index.model().index(index.row(),
                                            LOAD_CONFIG_COLUMN).data()

        # The config_name stored in the Table Model is composed of two
        # parts separated by a '|'. The first part indicates the configuration
        # type and can have values 'time' for configurations from past and
        # 'name' for named configurations.
        config_source_parts = config_source.split("|")

        if len(config_source_parts) == 2:
            norm_config_type = config_source_parts[0].lower().strip()

            if norm_config_type == "time":
                # For by "time" configs, the second part is the timestamp of
                # the configuration.
                get_network().onGetConfigurationFromPast(
                    device_id, time=config_source_parts[1], preview=False)
            elif norm_config_type == "name":
                get_network().onGetConfigurationFromName(
                    device_id, name=config_source_parts[1], preview=False)
            else:
                messagebox.show_warning(
                    text=f"Configurations of type {config_source_parts[0]} "
                         "cannot be loaded in the Configuration Editor.")
                return

            broadcast_event(KaraboEvent.ShowDevice,
                            {'deviceId': device_id, 'showTopology': True})


@register_binding_controller(
    ui_name="Recovery Report Table",
    klassname="RecoveryReportTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("RecoveryReportTable"),
    priority=-10,
    can_show_nothing=False)
class DisplayRecoveryReportTable(BaseFilterTableController):
    model = Instance(RecoveryReportTableModel, args=())

    def create_delegates(self):
        bindings = self.getBindings()
        for col in range(len(bindings)):
            self.tableWidget().setItemDelegateForColumn(col, None)
        btn_delegate = ButtonDelegate()
        self.tableWidget().setItemDelegateForColumn(LOAD_CONFIG_COLUMN,
                                                    btn_delegate)
