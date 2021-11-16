#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtWidgets import (
    QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget)
from traits.api import Instance

from karabogui.binding.api import VectorHashBinding
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
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

    # Other widgets
    search_label = Instance(QLineEdit)

    def create_widget(self, parent):

        # get the QTableView
        table_widget = super(
            DisplayDoocsMirrorTable, self).create_widget(parent)

        widget = QWidget(parent)
        widget_layout = QVBoxLayout()

        # search-related widgets
        search_layout = QHBoxLayout()
        self.search_label = QLineEdit(widget)
        clear_button = QPushButton("Clear", parent=widget)
        clear_button.clicked.connect(self.search_label.clear)
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(clear_button)

        # Complete widget layout and return widget
        widget_layout.addLayout(search_layout)
        widget_layout.addWidget(table_widget)
        widget.setLayout(widget_layout)

        return widget

    def create_delegates(self):
        """Create all the table delegates in the table element"""
        bindings = self.getBindings()
        # If we are readOnly, we erase all edit delegates
        for column in range(len(bindings)):
            self.tableWidget().setItemDelegateForColumn(column, None)
        button_delegate = ButtonDelegate()
        self.tableWidget().setItemDelegateForColumn(MIRROR_SCENELINK_COLUMN,
                                                    button_delegate)

    def createModel(self, model):
        """Create the filter model for the table"""
        filter_model = QSortFilterProxyModel()
        filter_model.setSourceModel(model)
        filter_model.setFilterRole(Qt.DisplayRole)
        filter_model.setFilterCaseSensitivity(False)
        filter_model.setFilterFixedString("")
        filter_model.setFilterKeyColumn(0)
        self.search_label.textChanged.connect(
            filter_model.setFilterFixedString)
        return filter_model
