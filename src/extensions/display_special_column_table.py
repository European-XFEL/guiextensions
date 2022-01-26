#############################################################################
# Author: <steffen.hauf@xfel.eu>
# Created on December 10, 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QLinearGradient
from qtpy.QtWidgets import QAction
from traits.api import Instance, WeakRef

from karabo.common.api import (
    KARABO_SCHEMA_MAX_EXC, KARABO_SCHEMA_MAX_INC, KARABO_SCHEMA_MIN_EXC,
    KARABO_SCHEMA_MIN_INC)
from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import register_binding_controller
from karabogui.controllers.edit.table import BaseTableController
from karabogui.controllers.table.model import TableModel
from karabogui.indicators import get_state_color

from .models.simple import SpecialColumnTableElementModel

BAR_COLOR_NEUTRAL = (112, 173, 255)
BAR_COLOR_LOW = (173, 255, 175)
BAR_COLOR_HIGH = (255, 143, 133)
EVEN_ALPHA = 150
ODD_ALPHA = 255
EMPTY_COLOR = QColor(255, 255, 255)

ONLINE_TEXT = "ONLINE"
OFFLINE_TEXT = "OFFLINE"
# we reuse state colors here for unified UI looks
ONLINE_COLOR = QColor(*get_state_color("ON"))
OFFLINE_COLOR = QColor(*get_state_color("ERROR"))
UNKNOWN_COLOR = QColor(*get_state_color("UNKNOWN"))
ON_OFF_MAP = {
    ONLINE_TEXT: ONLINE_COLOR,
    OFFLINE_TEXT: OFFLINE_COLOR
}


def is_progress_display_type(binding):
    """Return if the display type belongs to a state element"""
    return binding.display_type == "TableProgressBar"


def is_online_status_display_type(binding):
    """Return if the display type belongs to a state element"""
    return binding.display_type == "TableOnlineStatus"


def _interpolate_color(value):
    start = BAR_COLOR_LOW
    end = BAR_COLOR_HIGH
    r = (end[0] * value + start[0] * (1 - value))
    g = (end[1] * value + start[1] * (1 - value))
    b = (end[2] * value + start[2] * (1 - value))
    return r, g, b


class SpecialColumnTableModel(TableModel):

    def __init__(self, binding, set_edit_value, show_value, value_is_percent,
                 color_by_value, parent=None):
        super().__init__(binding, set_edit_value, parent=parent)
        self.show_value = show_value
        self.value_is_percent = value_is_percent
        self.color_by_value = color_by_value

    def data(self, index, role=Qt.DisplayRole):
        """Reimplemented function of QAbstractTableModel"""
        if not index.isValid():
            return None
        row, column = index.row(), index.column()

        if role == Qt.BackgroundRole:
            key = self._header[column]
            binding = self._bindings[key]
            if is_progress_display_type(binding):
                value = self._data[row][key]
                # clamp value to range
                min_val, max_val = self._eval_limits(binding)
                value = (value - min_val) / (max_val - min_val)
                bar_low = value - 1e-5
                bar_high = value + 1e-5
                if bar_low < 0:
                    bar_low = 0
                elif bar_high > 1.0:
                    bar_high = 1.0
                gradiant = QLinearGradient(
                    0, 0, self.parent().columnWidth(column), 0)
                alpha = EVEN_ALPHA if row % 2 == 0 else ODD_ALPHA

                if not self.color_by_value:
                    low_color = QColor(*BAR_COLOR_NEUTRAL, alpha)
                    gradiant.setColorAt(bar_low, low_color)
                else:
                    low_color = QColor(*BAR_COLOR_LOW, alpha)
                    med_color = QColor(*_interpolate_color(value),
                                       alpha)
                    gradiant.setColorAt(0, low_color)
                    gradiant.setColorAt(bar_low, med_color)

                gradiant.setColorAt(bar_high, EMPTY_COLOR)
                return QBrush(gradiant)
            elif is_online_status_display_type(binding):
                value = self._data[row][key]
                color = ON_OFF_MAP.get(value, UNKNOWN_COLOR)
                return QBrush(color)

        elif role == Qt.DisplayRole:
            key = self._header[column]
            binding = self._bindings[key]
            if is_progress_display_type(binding):
                value = self._data[row][key]
                if not self.show_value:
                    return ""
                if self.value_is_percent:
                    return f"{value:0.1f} %"
            elif is_online_status_display_type(binding):
                # harmonize display to upper value
                return self._data[row][key]

        return super().data(index, role=role)

    def _eval_limits(self, binding):
        attrs = binding.attributes
        min_val = attrs.get(KARABO_SCHEMA_MIN_INC,
                            attrs.get(KARABO_SCHEMA_MIN_EXC, 0))
        max_val = attrs.get(KARABO_SCHEMA_MAX_INC,
                            attrs.get(KARABO_SCHEMA_MAX_EXC, 1))

        return min_val, max_val


def is_table_compatible(binding):
    return "SpecialColumnTable" == binding.display_type


class BaseSpecialColumnTable(BaseTableController):
    _item_model = WeakRef(SpecialColumnTableModel, allow_none=True)

    def create_widget(self, parent):
        widget = super().create_widget(parent)

        showValueAction = QAction("Show Value", widget)
        showValueAction.triggered.connect(self._show_value)
        # update the context menu and keep track
        showValueAction.setCheckable(True)
        showValueAction.setChecked(self.model.show_value)
        widget.addAction(showValueAction)

        valueIsPercentAction = QAction("Value is %", widget)
        valueIsPercentAction.triggered.connect(self._value_is_percent)
        # update the context menu and keep track
        valueIsPercentAction.setCheckable(True)
        valueIsPercentAction.setChecked(self.model.value_is_percent)
        widget.addAction(valueIsPercentAction)

        colorByValueAction = QAction("Color by Value", widget)
        colorByValueAction.triggered.connect(self._color_by_value)
        # update the context menu and keep track
        colorByValueAction.setCheckable(True)
        colorByValueAction.setChecked(self.model.color_by_value)
        widget.addAction(colorByValueAction)

        return widget

    def _show_value(self):
        self.model.show_value = not self.model.show_value
        self.sourceModel().show_value = self.model.show_value
        self.value_update(self.proxy)

    def _value_is_percent(self):
        self.model.value_is_percent = not self.model.value_is_percent
        self.sourceModel().value_is_percent = self.model.value_is_percent
        self.value_update(self.proxy)

    def _color_by_value(self):
        self.model.color_by_value = not self.model.color_by_value
        self.sourceModel().color_by_value = self.model.color_by_value
        self.value_update(self.proxy)

    def _set_bindings(self, binding):
        """Configure the column schema hashes and keys

        The schema must not be `None` and is protected when calling this func.
        """
        if self._item_model is not None:
            self._item_model.setParent(None)
            self._item_model = None

        self._bindings = binding.bindings
        self._item_model = SpecialColumnTableModel(
            binding, self._on_user_edit, self.model.show_value,
            self.model.value_is_percent, self.model.color_by_value,
            parent=self._table_widget)
        self._item_model.set_readonly(self._readonly)
        model = self.createModel(self._item_model)
        self._table_widget.setModel(model)
        self._table_widget.set_bindings(binding.bindings)
        self.create_delegates()


# we cannot register on the Base class, as otherwise it cannot
# be reused
@register_binding_controller(ui_name='SpecialColumn Table',
                             klassname='SpecialColumnTable', priority=90,
                             binding_type=VectorHashBinding,
                             is_compatible=is_table_compatible)
class SpecialColumnTable(BaseSpecialColumnTable):
    model = Instance(SpecialColumnTableElementModel, args=())
