#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from enum import Enum

from qtpy.QtCore import QModelIndex, Qt
from qtpy.QtWidgets import QPushButton
from traits.api import Instance, List, String

from karabo.native import AccessMode
from karabogui.binding.api import BoolBinding, VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.controllers.table.api import BaseFilterTableController

from .icons import deselect_all, invert_select, select_all
from .models.api import SelectionTableModel


class SelectionMethod(Enum):
    ALL = "all"
    NONE = "none"
    INVERT = "invert"


NO_COLUMN_TOOLTIP = "No selectable column in table"


def _get_selection_column(bindings):
    RO = AccessMode.READONLY
    num_selection_cols = 0
    sel_col_index = None
    for index, binding in enumerate(bindings.values()):
        if isinstance(binding, BoolBinding) and binding.access_mode is not RO:
            if with_display_type("TableSelection")(binding):
                num_selection_cols += 1
                sel_col_index = index
    return num_selection_cols, sel_col_index


def _is_compatible(base_binding):
    bindings = base_binding.bindings
    num_selection_cols, _ = _get_selection_column(bindings)
    # there should be exactly one selection column
    return num_selection_cols == 1


@register_binding_controller(
    ui_name="Selection Table",
    klassname="SelectionTable",
    is_compatible=_is_compatible,
    binding_type=VectorHashBinding,
    priority=-10,
    can_edit=True,
    can_show_nothing=False)
class SelectionTable(BaseFilterTableController):
    model = Instance(SelectionTableModel, args=())
    originalToolTip = String()
    buttons = List(Instance(QPushButton))

    def create_widget(self, parent):
        table_widget = super().create_widget(parent)
        top_layout = table_widget.layout()

        # we want ta add to the horizontal layout after the "Clear Button"
        hor_layout = top_layout.children()[0]
        select_all_button = QPushButton("", parent=table_widget)
        select_all_button.setIcon(select_all.icon)
        select_all_button.setToolTip("Select All in Filtered View")
        select_all_button.clicked.connect(self._select_all)
        self.buttons.append(select_all_button)

        select_none_button = QPushButton("", parent=table_widget)
        select_none_button.setIcon(deselect_all.icon)
        select_none_button.setToolTip("De-Select All in Filtered View")
        select_none_button.clicked.connect(self._deselect_all)
        self.buttons.append(select_none_button)

        select_invert_button = QPushButton("", parent=table_widget)
        select_invert_button.setIcon(invert_select.icon)
        select_invert_button.setToolTip("Invert Selection of Filtered View")
        select_invert_button.clicked.connect(self._invert_selection)
        self.buttons.append(select_invert_button)

        hor_layout.addWidget(select_all_button)
        hor_layout.addWidget(select_none_button)
        hor_layout.addWidget(select_invert_button)

        self.originalToolTip = table_widget.toolTip()

        return table_widget

    def binding_update(self, proxy):
        super().binding_update(proxy)
        num_cols, column = _get_selection_column(proxy.binding.bindings)
        ok = num_cols == 1
        if not ok or column is None:
            self.tableWidget().setToolTip(NO_COLUMN_TOOLTIP)
            # disable all buttons
            for button in self.buttons:
                button.setEnabled(False)
        else:
            self.tableWidget().setToolTip(self.originalToolTip)
            # enable all buttons
            for button in self.buttons:
                button.setEnabled(True)

    def _change_selection(self, method):
        model = self._item_model
        filter_model = self.tableWidget().model()
        _,  column = _get_selection_column(self._bindings)

        for row in range(model.rowCount()):
            index = model.index(row, column, QModelIndex())
            # check if its in the filtered view
            if not filter_model.mapFromSource(index).isValid():
                continue
            if method is SelectionMethod.ALL:
                value = True
            elif method is SelectionMethod.NONE:
                value = False
            elif method is SelectionMethod.INVERT:
                existing = model.data(index, role=Qt.CheckStateRole)
                value = existing != Qt.Checked

            self._item_model.setData(index, value, Qt.DisplayRole)

    def _select_all(self):
        self._change_selection(SelectionMethod.ALL)

    def _deselect_all(self):
        self._change_selection(SelectionMethod.NONE)

    def _invert_selection(self):
        self._change_selection(SelectionMethod.INVERT)
