#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtWidgets import QDialog, QMenu
from traits.api import Bool, Instance

from karabo.common.api import WeakMethodRef
from karabo.native import Hash
from karabogui.api import (
    BaseFilterTableController, VectorHashBinding, call_device_slot,
    get_reason_parts, icons, is_device_online, messagebox,
    register_binding_controller, with_display_type)

from .dialogs.api import DeviceConfigurationPreview
from .models.api import DeviceReconfigurationTableModel
from .utils import gui_version_compatible

COMPARE_NO_CHANGES = "No changes"
COMPARE_CHANGES = "Changes detected"
COMPARE_UNKNOWN = "No data"
DEVICE_ID_COLUMN = 0


@register_binding_controller(
    ui_name="Device Reconfiguration Table",
    klassname="DeviceReconfigurationTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("DeviceReconfigurationTable"),
    priority=-10,
    can_show_nothing=False)
class DisplayDeviceReconfigurationTable(BaseFilterTableController):
    model = Instance(DeviceReconfigurationTableModel, args=())
    hasCustomMenu = Bool(True)

    def create_widget(self, parent):
        table_widget = super().create_widget(parent)
        self.tableWidget().doubleClicked.connect(self.action_get_config)
        return table_widget

    def custom_menu(self, pos):
        """Subclassed method for own custom menu

        :param: pos: The position of the context menu event
        """
        menu = QMenu(self.tableWidget())
        if self.currentIndex().isValid():
            if gui_version_compatible(2, 16):
                open_scene_action = menu.addAction("Open Device Scene")
                open_scene_action.setIcon(icons.scenelink)
                open_scene_action.triggered.connect(self.action_open_scene)
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

    def action_open_scene(self):
        device_id = self._get_selected_device()
        if is_device_online(device_id):
            from karabogui.api import retrieve_default_scene
            retrieve_default_scene(device_id)
        else:
            msg = ("Unable to retrieve default scene. "
                   f"Device {device_id} is not reachable.")
            messagebox.show_warning(msg, parent=self.widget)

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
            current_timestamp = data.get("new_timestamp")
            requested_config = data.get("old", Hash())
            requested_timestamp = data.get("old_timestamp")
            dialog = DeviceConfigurationPreview(
                device_id, current_config, requested_config,
                current_timestamp, requested_timestamp, parent=self.widget)
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
            data = reply["payload"].get("data", Hash())
            # Compatibility, always no changes
            changes = data.get("changes", COMPARE_NO_CHANGES)
            if changes == COMPARE_NO_CHANGES:
                text = "all changes could be applied successfully."
            elif changes == COMPARE_CHANGES:
                text = ("however, there are still differences in comparing "
                        "both actual and preset configurations.")
            elif changes == COMPARE_UNKNOWN:
                text = "however, no information about changes is available."
            else:
                text = "unknown change type"

            messagebox.show_information(f"Configuration applied: {text}",
                                        parent=self.widget)

    def _get_selected_device(self):
        row = self.currentIndex().row()
        model = self.tableWidget().model()
        _, device_id = model.get_model_data(row, DEVICE_ID_COLUMN)
        return device_id
