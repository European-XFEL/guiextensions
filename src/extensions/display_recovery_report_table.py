#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtWidgets import QDialog
from traits.api import Bool, Instance

from karabo.common.api import WeakMethodRef
from karabo.native import Hash
from karabogui.api import (
    BaseFilterTableController, VectorHashBinding, call_device_slot,
    get_reason_parts, icons, is_device_online, messagebox,
    register_binding_controller, retrieve_default_scene, with_display_type)

from .dialogs.api import DeviceConfigurationPreview
from .models.api import RecoveryReportTableModel


@register_binding_controller(
    ui_name="Recovery Report Table",
    klassname="RecoveryReportTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("RecoveryReportTable"),
    priority=-10,
    can_show_nothing=False)
class DisplayRecoveryReportTable(BaseFilterTableController):
    model = Instance(RecoveryReportTableModel, args=())
    hasCustomMenu = Bool(True)

    def create_widget(self, parent):
        table_widget = super().create_widget(parent)
        self.tableWidget().doubleClicked.connect(self.action_get_config)
        return table_widget

    def custom_menu(self, pos):
        """Subclassed method for own custom menu

        :param: pos: The position of the context menu event
        """
        menu = self.get_basic_menu()
        if self.currentIndex().isValid():
            # Enable this when retrieve_default_scene works correctly
            # open_scene_action = menu.addAction("Open Device Scene")
            # open_scene_action.setIcon(icons.scenelink)
            # open_scene_action.triggered.connect(self.action_open_device_scene)
            menu.addSeparator()
            apply_config_action = menu.addAction(
                "View and Apply Configuration")
            apply_config_action.setIcon(icons.enum)
            apply_config_action.triggered.connect(self.action_get_config)
        menu.exec_(self.tableWidget().viewport().mapToGlobal(pos))

    def action_get_config(self):
        device_id = self._get_selected_device()
        call_device_slot(WeakMethodRef(self.handle_get_configuration),
                         self.getInstanceId(), "requestAction",
                         deviceId=device_id,
                         action="getConfiguration")

    def action_open_device_scene(self):
        device_id = self._get_selected_device()
        if is_device_online(device_id):
            retrieve_default_scene(device_id)
        else:
            msg = ("Unable to retrieve default scene. "
                   f"Device {device_id} is not reachable.")
            messagebox.show_warning(msg)

    def handle_get_configuration(self, success, reply):
        """Handler for request `getConfiguration`"""
        if not success:
            # In case if no success, the reply is the reason
            reason, details = get_reason_parts(reply)
            messagebox.show_error(
                "Get Configuration request could not be fulfilled: "
                f"{reason}", details=details, parent=self.widget)
        else:
            data = reply["payload"]["data"]
            device_id = data["deviceId"]
            current_config = data.get("new", Hash())
            requested_config = data.get("old", Hash())
            dialog = DeviceConfigurationPreview(device_id, current_config,
                                                requested_config,
                                                parent=self.widget)
            if dialog.exec() == QDialog.Accepted:
                call_device_slot(WeakMethodRef(self.handle_config_apply),
                                 self.getInstanceId(), "requestAction",
                                 deviceId=device_id, config=requested_config,
                                 action="applyConfiguration")

    def handle_config_apply(self, success, reply):
        """Handler for request `applyConfiguration`"""
        if not success:
            # In case if no success, the reply is the reason
            reason, details = get_reason_parts(reply)
            messagebox.show_error(
                "Apply Configuration request could not be fulfilled: "
                f"{reason}", details=details, parent=self.widget)
        else:
            messagebox.show_information("Configuration applied")

    def _get_selected_device(self):
        header = list(self.getBindings().keys())
        model = self.tableWidget().model()
        row = self.currentIndex().row()
        _, device_id = model.get_model_data(row, header.index("deviceId"))
        return device_id
