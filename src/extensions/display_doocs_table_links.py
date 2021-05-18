#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections import namedtuple
from functools import partial

from PyQt5.QtCore import (
    QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, pyqtSlot)

from PyQt5.QtWidgets import (
    QHeaderView, QMenu, QPushButton, QStyle, QStyledItemDelegate,
    QTableView, QVBoxLayout)

from traits.api import Instance, WeakRef

from karabogui import messagebox
from karabogui.binding.api import VectorHashBinding, get_editor_value
from karabogui.controllers.api import (
    with_display_type, BaseBindingController, register_binding_controller)
from karabogui.request import call_device_slot#, get_scene_from_server

from .models.simple import DoocsManagerTableModel, DoocsMirrorTableModel

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

serviceEntry = namedtuple('serviceEntry', MIRROR_ENTRY_LABELS)


def request_handler(device_id, action, success, reply):
    """Callback handler for a request to the DOOCS manager"""
    if not success or not reply.get('payload.success', False):
        msg = (f"Error: Properties could not be updated. "
               "See the device server log for details.")
        messagebox.show_warning(msg, title='Mirror Service Failed')
    return


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
        # NOTE: For future use (as for opening a mirror scene)
        column = index.column()
        relevant_list = [MIRROR_SCENELINK_COLUMN]
        if column in relevant_list:
            return True, MIRROR_COLUMN_TEXT[column]

        return False, ""

    def updateEditorGeometry(self, button, option, index):
        """Relevant cells are displayed as buttons."""
        # NOTE: For future use (as for opening a mirror scene)
        relevant, text = self._is_relevant_column(index)
        if relevant:
            button.setGeometry(option.rect)
            button.setText(text)

    def setEditorData(self, button, index):
        """Relevant cells are displayed as buttons."""
        # NOTE: For future use (as for opening a mirror scene)
        relevant, text = self._is_relevant_column(index)
        if relevant:
            button.setText(text)
        else:
            super(ButtonDelegate, self).setEditorData(button, index)

    def paint(self, painter, option, index):
        """Relevant cells are displayed as buttons."""
        # NOTE: For future use (as for opening a mirror scene)
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

    def _show_properties(self, server):
        """Show The custom context menu of a reconfigurable table element"""
        handler = partial(request_handler, self.device_id, server)
        call_device_slot(handler, self.device_id, 'requestManagerAction',
                         action=server)

    @pyqtSlot(QModelIndex)
    def cellClicked(self, index):
        """Action to take when a cell is clicked."""        
        device_id = self.parent.model().index(index.row(), 0).data()
        print("CLICKED: ", device_id)
        #get_scene_from_server(device_id, "overview")#, project=None,
        #target_window=SceneTargetWindow.Dialog):

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
            if column == MIRROR_SCENELINK_COLUMN:
                #provide a deviceSceneLink: to be implemented
                pass

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
        self.table_model = DoocsMirrorTable(parent=table_view)

        # here we set our model
        table_view.setModel(self.table_model)
        btn_delegate = ButtonDelegate(
            parent=table_view, device_id=self.proxy.root_proxy.device_id)
        table_view.setItemDelegateForColumn(
            MIRROR_NAME_COLUMN, btn_delegate)
        self.delegate = btn_delegate

        header = table_view.horizontalHeader()
        header.setDefaultSectionSize(50)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(table_view)

        return widget

    def binding_update(self, proxy):
        """This method is executed after a schema update of the device"""
        pass

    def value_update(self, proxy):
        """This method is executed with a value update of the table"""
        value = get_editor_value(proxy, [])
        self.table_model.update_model(value)
        value = proxy.value
