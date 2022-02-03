#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on October 15, 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from qtpy.QtCore import QModelIndex, QSortFilterProxyModel, Qt
from qtpy.QtWidgets import (
    QComboBox, QHBoxLayout, QLayout, QLineEdit, QPushButton, QVBoxLayout,
    QWidget)
from traits.api import Instance

from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.controllers.table.api import BaseTableController

from .models.api import HistorianTableModel

META_DATA_COLUMN = 3
ON_OFF_COLUMN = 2

ALL_DEVICES = "All Devices"
ONLINE_DEVICES = "Online Devices"
OFFLINE_DEVICES = "Offline Devices"


class HistorianFilterModel(QSortFilterProxyModel):
    """The filter model to filter for online and offline devices
    """

    def __init__(self, source_model=None, parent=None):
        super().__init__(parent)
        self.setSourceModel(source_model)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterRole(Qt.DisplayRole)
        self.setFilterKeyColumn(0)
        self._filter_status = None

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        source_index = model.index(source_row, self.filterKeyColumn(),
                                   source_parent)
        if source_index.isValid():
            data = source_index.data()
            if not data:
                return True
            if self._filter_status is None:
                return super().filterAcceptsRow(
                    source_row, source_parent)
            else:
                match = super().filterAcceptsRow(
                    source_row, source_parent)
                on_off = model.index(source_index.row(), ON_OFF_COLUMN,
                                     QModelIndex())
                match_on = self._filter_status == on_off.data()
                return match and match_on

        return super().filterAcceptsRow(source_row, source_parent)

    def setFilterStatus(self, text):
        """Set a filter status for the filtering"""
        if text == ALL_DEVICES:
            self._filter_status = None
        elif text == ONLINE_DEVICES:
            self._filter_status = "ONLINE"
        elif text == OFFLINE_DEVICES:
            self._filter_status = "OFFLINE"
        else:
            self._filter_status = None
        self.invalidateFilter()


@register_binding_controller(
    ui_name="Operational Historian Table",
    klassname="HistorianTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("HistorianTable"),
    priority=-10, can_show_nothing=False)
class DisplayHistorianTable(BaseTableController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(HistorianTableModel, args=())
    searchLabel = Instance(QLineEdit)
    filterCombo = Instance(QComboBox)

    def create_widget(self, parent):
        table_widget = super().create_widget(parent)
        table_widget.setSortingEnabled(True)

        widget = QWidget(parent)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSizeConstraint(QLayout.SetNoConstraint)

        hor_layout = QHBoxLayout()
        hor_layout.setContentsMargins(0, 0, 0, 0)
        hor_layout.setSizeConstraint(QLayout.SetNoConstraint)

        self.searchLabel = QLineEdit(widget)
        clear_button = QPushButton("Clear", parent=widget)
        clear_button.clicked.connect(self.searchLabel.clear)
        hor_layout.addWidget(self.searchLabel)
        hor_layout.addWidget(clear_button)

        # Complete widget layout and return widget
        widget_layout.addLayout(hor_layout)
        self.filterCombo = QComboBox()
        self.filterCombo.addItems([ALL_DEVICES,
                                   ONLINE_DEVICES,
                                   OFFLINE_DEVICES])
        widget_layout.addWidget(self.filterCombo)
        widget_layout.addWidget(table_widget)
        widget.setLayout(widget_layout)

        return widget

    def createModel(self, model):
        """Create the filter model for the table"""
        filter_model = HistorianFilterModel()
        filter_model.setSourceModel(model)
        filter_model.setFilterRole(Qt.DisplayRole)
        filter_model.setFilterCaseSensitivity(False)
        filter_model.setFilterFixedString("")
        self.searchLabel.textChanged.connect(filter_model.setFilterFixedString)
        self.filterCombo.currentTextChanged.connect(
            filter_model.setFilterStatus)
        return filter_model
