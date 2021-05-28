#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections import namedtuple

from PyQt5.QtCore import (
    QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, pyqtSlot)

from PyQt5.QtGui import QBrush, QColor

from PyQt5.QtWidgets import (
    QHBoxLayout, QHeaderView, QLineEdit, QPushButton, QStyle,
    QStyledItemDelegate, QTableView, QVBoxLayout)

from traits.api import Instance, WeakRef

from karabogui.binding.api import VectorHashBinding, get_editor_value
from karabogui.controllers.api import (
    with_display_type, BaseBindingController, register_binding_controller)
from karabogui.util import get_scene_from_server  # until karabo 2.10.x
# from karabogui.request import get_scene_from_server  # from 2.11.0

from .models.simple import DoocsMirrorTableModel

MIRROR_NAME_COLUMN = 0
MIRROR_STATE_COLUMN = 1
MIRROR_SCENELINK_COLUMN = 2
MIRROR_STATUS_COLUMN = 3
MIRROR_COLUMN_TEXT = {
    MIRROR_NAME_COLUMN: "Name",
    MIRROR_STATE_COLUMN: "State",
    MIRROR_SCENELINK_COLUMN: "SceneLink",
    MIRROR_STATUS_COLUMN: "Status",
}
MIRROR_HEADER_LABELS = [text for text in MIRROR_COLUMN_TEXT.values()]
MIRROR_ENTRY_LABELS = [text[0].lower()+text[1:] for column, text
                       in MIRROR_COLUMN_TEXT.items() if column < 5]
RELEVANT_LIST = [MIRROR_SCENELINK_COLUMN]

serviceEntry = namedtuple('serviceEntry', MIRROR_ENTRY_LABELS)


def get_state_brush(state):
    """Decorate a cell with proper color according to the input string."""
    if state == "ON":
        return QBrush(QColor(120, 255, 0))
    elif state == "ERROR":
        return QBrush(QColor(255, 0, 0))
    elif state == "INIT":
        return QBrush(QColor(180, 255, 255))
    elif state == "UNKNOWN":
        return QBrush(QColor(255, 140, 0))


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, device_id=None):
        super(ButtonDelegate, self).__init__(parent)
        self.clickable = True
        self.device_id = device_id
        self._button = QPushButton("")
        self._button.hide()
        self.parent = parent
        # Action to take when left-clicking
        parent.clicked.connect(self.cellClicked)

    def _is_relevant_column(self, index):
        """Return whether a column is relevant to trigger an action
        upon clicking.
        """
        column = index.column()
        if column in RELEVANT_LIST:
            return True, MIRROR_COLUMN_TEXT[column]
        return False, ""

    def paint(self, painter, option, index):
        """Relevant cells are displayed as buttons."""
        relevant, text = self._is_relevant_column(index)
        if relevant:
            self._button.setGeometry(option.rect)
            self._button.setText(text)
            if option.state == QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            pixmap = self._button.grab()
            self._button.setEnabled(self.clickable)
            painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap)
        else:
            super(ButtonDelegate, self).paint(painter, option, index)

    @pyqtSlot(QModelIndex)
    def cellClicked(self, index):
        """Action to take when a relevant cell is clicked."""
        device_id = self.parent.model().index(index.row(), 0).data()
        scene_id = self.parent.model().index(index.row(), 2).data()
        relevant, _ = self._is_relevant_column(index)
        if relevant and scene_id is not None:
            get_scene_from_server(device_id, scene_id)
        return


class DoocsMirrorTable(QAbstractTableModel):
    """ A class which describes the relevant data (model) of a doocs manager
    device to present in a table view.
    """

    def __init__(self, parent=None):
        super(DoocsMirrorTable, self).__init__(parent)
        self._table_data = []
        self.parent = parent

    def initialize(self, value):
        self.beginResetModel()
        for index, row_data in enumerate(value):
            self._table_data[index] = serviceEntry(**row_data)
        self.endResetModel()

    def update_model(self, value):
        num_rows = self.rowCount()
        new_rows = len(value)
        difference = new_rows - num_rows

        # Update our book keeping Hash first before proceeding!
        for index, row_data in enumerate(value):
            if index < num_rows:
                self._table_data[index] = serviceEntry(**row_data)
            else:
                row = self.rowCount()
                self.beginInsertRows(QModelIndex(), row, row)
                self._table_data.append(serviceEntry(**row_data))
                self.endInsertRows()

        if difference < 0:
            for _ in range(abs(difference)):
                # NOTE: We can safely pop the data, since the update
                # overwrites! The rows start at 0!
                row = self.rowCount()
                self.beginRemoveRows(QModelIndex(), row - 1, row)
                self._table_data.pop()
                self.endRemoveRows()

        # XXX: We are nifty here and simply announce a complete layoutChange
        # This turns out to be several times faster than doing a dataChange
        # for every item. Avoid races by doing this close together...
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return MIRROR_HEADER_LABELS[section]

    def rowCount(self, parent=QModelIndex()):
        return len(self._table_data)

    def columnCount(self, parent=QModelIndex()):
        return len(MIRROR_HEADER_LABELS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        entry = self._table_data[index.row()]
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if index.column() < len(MIRROR_ENTRY_LABELS):
                return str(entry[index.column()])
        elif role == Qt.BackgroundRole:
            column = index.column()
            if column == MIRROR_STATE_COLUMN:
                # align the cell color with the displayed state
                return get_state_brush(entry.state)

        return None


@register_binding_controller(
    ui_name='Doocs Device Table',
    klassname='DoocsMirrorTable',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type('WidgetNode|DoocsMirrorTable'),
    priority=-10, can_show_nothing=False)
class DisplayDoocsMirrorTable(BaseBindingController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DoocsMirrorTableModel, args=())
    table_model = WeakRef(QAbstractTableModel)
    delegate = WeakRef(ButtonDelegate)

    def create_widget(self, parent):
        widget = QTableView(parent=parent)
        layout = QVBoxLayout(widget)
        # we do not want margins around the widget (table)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        # The main table view!
        table_view = QTableView(widget)
        table_view.setSortingEnabled(True)
        self.table_model = DoocsMirrorTable(parent=table_view)

        # ==>Set up the filter model
        filter_model = QSortFilterProxyModel(parent=table_view)
        filter_model.setSourceModel(self.table_model)
        filter_model.setFilterRole(Qt.DisplayRole)
        filter_model.setFilterCaseSensitivity(False)
        filter_model.setFilterFixedString("")
        filter_model.setFilterKeyColumn(0)

        # here we set our model
        table_view.setModel(filter_model)
        btn_delegate = ButtonDelegate(
            parent=table_view, device_id=self.proxy.root_proxy.device_id)
        table_view.setItemDelegateForColumn(
            MIRROR_SCENELINK_COLUMN, btn_delegate)
        self.delegate = btn_delegate

        # table header config
        header = table_view.horizontalHeader()
        header.setDefaultSectionSize(50)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignLeft)
        layout.addWidget(table_view)

        # search widget
        search_layout = QHBoxLayout()
        search_line = QLineEdit(parent=widget)
        search_line.textChanged.connect(filter_model.setFilterFixedString)
        search_layout.addWidget(search_line)
        layout.addLayout(search_layout)

        return widget

    def binding_update(self, proxy):
        """This method is executed after a schema update of the device"""
        pass

    def value_update(self, proxy):
        """This method is executed with a value update of the table"""
        value = get_editor_value(proxy, [])
        self.table_model.update_model(value)
        value = proxy.value
