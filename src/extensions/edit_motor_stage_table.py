#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCompleter, QLineEdit, QStyledItemDelegate
from traits.api import Instance

from karabo.common.api import Interfaces
from karabo.native import Hash, is_equal
from karabogui.api import (
    BaseTableController, PropertyProxy, VectorHashBinding, get_binding_value,
    get_topology, register_binding_controller, with_display_type)

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
        editor.setCompleter(QCompleter(value))
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
        editor.setCompleter(QCompleter(filtered))
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
class EditableAssignmentTable(BaseTableController):
    model = Instance(MotorAssignmentTableModel, args=())

    stageOptions = Instance(PropertyProxy)

    def binding_update(self, proxy):
        super().binding_update(proxy)
        self.stageOptions = PropertyProxy(root_proxy=proxy.root_proxy,
                                          path="stageOptions")
        # Apply the delegates
        terminal_delegate = MotorCompleterDelegate(parent=self.tableWidget())
        stage_delegate = CompleterDelegate(self.stageOptions,
                                           parent=self.tableWidget())

        delegates = {TERMINAL_COLUMN: terminal_delegate,
                     STAGE_COLUMN: stage_delegate}
        for column, delegate in delegates.items():
            self.tableWidget().setItemDelegateForColumn(column, delegate)
