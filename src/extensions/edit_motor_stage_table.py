#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import QModelIndex, Qt
from qtpy.QtWidgets import (
    QCompleter, QDialog, QLineEdit, QMenu, QStyledItemDelegate)
from traits.api import Bool, Instance

from karabo.common.api import Interfaces, WeakMethodRef
from karabo.native import Hash, is_equal
from karabogui.api import (
    BaseFilterTableController, PropertyProxy, VectorHashBinding,
    call_device_slot, get_binding_value, get_reason_parts, get_topology, icons,
    messagebox, register_binding_controller, with_display_type)

from .dialogs.api import MotorConfigurationPreview
from .models.api import MotorAssignmentTableModel

TERMINAL_COLUMN = 0
STAGE_COLUMN = 1


class CompleterDelegate(QStyledItemDelegate):
    def __init__(self, proxy, parent=None):
        super().__init__(parent)
        self.proxy = proxy

    def createEditor(self, parent, option, index):
        """Reimplemented function of QStyledItemDelegate"""
        editor = QLineEdit(parent)
        value = get_binding_value(self.proxy, [])
        completer = QCompleter(value)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        editor.setCompleter(completer)
        return editor

    def setModelData(self, editor, model, index):
        """Reimplemented function of QStyledItemDelegate"""
        old = index.model().data(index, Qt.DisplayRole)
        new = editor.text()
        if not is_equal(old, new):
            model.setData(index, new, Qt.EditRole)
            self.commitData.emit(self.sender())


class MotorCompleterDelegate(QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        """Reimplemented function of QStyledItemDelegate"""
        editor = QLineEdit(parent)
        topo = get_topology()._system_hash.get("device", Hash())
        filtered = []
        for k, _, a in topo.iterall():
            interfaces = a.get("interfaces", 0)
            if self._check_interface(interfaces, Interfaces.Motor):
                filtered.append(k)
        completer = QCompleter(filtered)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        editor.setCompleter(completer)
        return editor

    def _check_interface(self, mask, bit):
        return (mask & bit) == bit

    def setModelData(self, editor, model, index):
        """Reimplemented function of QStyledItemDelegate"""
        old = index.model().data(index, Qt.DisplayRole)
        new = editor.text()
        if not is_equal(old, new):
            model.setData(index, new, Qt.EditRole)
            self.commitData.emit(self.sender())


@register_binding_controller(
    ui_name="Motor Stage Assignment Table",
    klassname="MotorStageAssignmentTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("MotorStageAssignmentTable"),
    can_edit=True, priority=-10, can_show_nothing=True)
class EditableAssignmentTable(BaseFilterTableController):
    model = Instance(MotorAssignmentTableModel, args=())

    # Implement own custom menu
    hasCustomMenu = Bool(True)
    stageOptions = Instance(PropertyProxy)

    def create_delegates(self):
        self.stageOptions = PropertyProxy(root_proxy=self.proxy.root_proxy,
                                          path="stageOptions")
        # Apply the delegates
        terminal_delegate = MotorCompleterDelegate(parent=self.tableWidget())
        stage_delegate = CompleterDelegate(self.stageOptions,
                                           parent=self.tableWidget())

        delegates = {TERMINAL_COLUMN: terminal_delegate,
                     STAGE_COLUMN: stage_delegate}
        for column, delegate in delegates.items():
            self.tableWidget().setItemDelegateForColumn(column, delegate)

    def custom_menu(self, pos):
        """Subclassed method for own custom menu

        :param: pos: The position of the context menu event
        """
        menu = self.get_basic_menu()
        if self.currentIndex().isValid():
            menu.addSeparator()
            request_save = menu.addAction("Request Save Configuration")
            request_save.setIcon(icons.save)
            request_save.triggered.connect(self.action_config_save)
            # Don't allow this action when we have an `edit_value`
            enabled = self.proxy.edit_value is None
            request_save.setEnabled(enabled)
        menu.exec_(self.tableWidget().viewport().mapToGlobal(pos))

    def action_config_save(self):
        """Action to save the configuration of the current terminal"""
        row = self.currentIndex().row()
        model = self.sourceModel()
        terminalId = model.index(row, TERMINAL_COLUMN).data(Qt.DisplayRole)
        stageQrCode = model.index(row, STAGE_COLUMN).data(Qt.DisplayRole)
        call_device_slot(WeakMethodRef(self.handle_view_configuration),
                         self.getInstanceId(), "requestAction",
                         terminalId=terminalId, stageQrCode=stageQrCode,
                         action="viewConfiguration")

    def handle_view_configuration(self, success, reply):
        """Handler for request `viewConfiguration`"""
        if not success:
            # In case if no success, the reply is the reason
            reason, details = get_reason_parts(reply)
            messagebox.show_error("View request could not be fulfilled: "
                                  f"{reason}", details=details,
                                  parent=self.widget)
        else:
            payload = reply["payload"]
            old = payload["old"]
            new = payload["new"]
            terminalId = payload["terminalId"]
            stageQrCode = payload["stageQrCode"]
            dialog = MotorConfigurationPreview(
                old, new, terminalId, stageQrCode, parent=self.widget)
            if dialog.exec() == QDialog.Accepted:
                call_device_slot(WeakMethodRef(self.handle_config_save),
                                 self.getInstanceId(), "requestAction",
                                 terminalId=terminalId,
                                 stageQrCode=stageQrCode,
                                 configuration=new,
                                 action="saveConfiguration")

    def handle_config_save(self, success, reply):
        """Handler for request `saveConfiguration`"""
        if not success:
            # In case if no success, the reply is the reason
            reason, details = get_reason_parts(reply)
            messagebox.show_error(
                f"Save request could not be fulfilled: {reason}",
                details=details, parent=self.widget)
        else:
            # In Karabo 2.16.X provide information about the request here ...
            messagebox.show_information(
                "Configuration has been saved!", parent=self.widget)

    # Temporary implementation for Karabo < 2.16.X
    # -----------------------------------------------------------------------

    def get_basic_menu(self):
        """Used by subclassed controller to get the basic menu"""
        index = self.currentIndex()
        menu = QMenu(parent=self.tableWidget())
        if index.isValid():
            up_action = menu.addAction(icons.arrowFancyUp, "Move Row Up")
            up_action.triggered.connect(self.move_row_up)
            down_action = menu.addAction(icons.arrowFancyDown, "Move Row Down")
            down_action.triggered.connect(self.move_row_down)
            menu.addSeparator()

            add_action = menu.addAction(icons.add, "Add Row below")
            add_action.triggered.connect(self.add_row)
            du_action = menu.addAction(icons.editCopy, "Duplicate Row below")
            du_action.triggered.connect(self.duplicate_row)

            remove_action = menu.addAction(icons.delete, "Delete Row")
            remove_action.triggered.connect(self.remove_row)

            # Set actions enabled or disabled!
            num_row = self.tableWidget().model().rowCount() - 1
            up_action.setEnabled(index.row() > 0)
            down_action.setEnabled(index.row() < num_row)
            remove_action.setEnabled(num_row >= 0)
        else:
            add_action = menu.addAction(icons.add, "Add Row below")
            add_action.triggered.connect(self.add_row)

        return menu

    def add_row(self):
        row = self.currentIndex().row()
        self._item_model.insertRows(row + 1, 1, QModelIndex())

    def duplicate_row(self):
        row = self.currentIndex().row()
        self._item_model.duplicate_row(row)

    def move_row_up(self):
        row = self.currentIndex().row()
        self._item_model.move_row_up(row)
        self._table_widget.selectRow(row - 1)

    def move_row_down(self):
        row = self.currentIndex().row()
        self._item_model.move_row_down(row)
        self._table_widget.selectRow(row + 1)

    def remove_row(self):
        index = self.currentIndex()
        self._item_model.removeRows(index.row(), 1, QModelIndex())
