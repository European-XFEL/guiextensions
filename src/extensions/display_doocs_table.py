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
from karabogui.request import call_device_slot

from .models.simple import DoocsManagerTableModel

MANAGER_SERVER_COLUMN = 0
MANAGER_PROPERTY_COLUMN = 1
MANAGER_COLUMN_TEXT = {
    0: "Server",
    1: "Properties",
}
MANAGER_HEADER_LABELS = [text for text in MANAGER_COLUMN_TEXT.values()]
MANAGER_ENTRY_LABELS = [text.lower() for column, text
                        in MANAGER_COLUMN_TEXT.items() if column < 5]

serviceEntry = namedtuple('serviceEntry', MANAGER_ENTRY_LABELS)


def request_handler(device_id, action, success, reply):
    """Callback handler for a request to the DOOCS manager"""
    if not success or not reply.get('payload.success', False):
        msg = (f"Error: Properties could not be updated. "
               "See the device server log for details.")
        messagebox.show_warning(msg, title='Manager Service Failed')
    return


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, device_id=None):
        super(ButtonDelegate, self).__init__(parent)
        self.clickable = True
        self.device_id = device_id
        self._button = QPushButton("")
        self._button.hide()
        self.parent = parent
        # show a context menu by right-clicking
        parent.setContextMenuPolicy(Qt.CustomContextMenu)
        parent.customContextMenuRequested.connect(self._context_menu)

    def _is_relevant_column(self, index):
        """Return whether a column is relevant to trigger an action
        upon clicking.
        """
        # NOTE: For future use (as for opening a mirror scene)
        column = index.column()
        relevant_list = []
        if column in relevant_list:
            return True, MANAGER_COLUMN_TEXT[column]

        return False, ""

    def _context_menu(self, pos):
        """The custom context menu of a reconfigurable table element"""
        selection_model = self.parent.selectionModel()
        if selection_model is None:
            # XXX: We did not yet receive a schema and thus have no table and
            # selection model!
            return
        index = selection_model.currentIndex()
        if index.isValid():

            menu = QMenu(parent=self.parent)

            label = self.parent.model().index(index.row(), 0).data()
            menu.addAction(label)
            menu.addSeparator()
            show_properties_action = menu.addAction(
                'Show Available Properties')
            show_properties_action.triggered.connect(
                partial(self._show_properties, label))

            menu.exec_(self.parent.viewport().mapToGlobal(pos))

    def _show_properties(self, server):
        """Show The custom context menu of a reconfigurable table element"""
        handler = partial(request_handler, self.device_id, server)
        call_device_slot(handler, self.device_id, 'requestManagerAction',
                         action=server)


class DoocsManagerTable(QAbstractTableModel):
    """ A class which describes the relevant data (model) of a doocs manager
    device to present in a table view.
    """

    def __init__(self, parent=None):
        super(DoocsManagerTable, self).__init__(parent)
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
            return MANAGER_HEADER_LABELS[section]

    def rowCount(self, parent=QModelIndex()):
        return len(self._table_data)

    def columnCount(self, parent=QModelIndex()):
        return len(MANAGER_HEADER_LABELS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        entry = self._table_data[index.row()]
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if index.column() < len(MANAGER_ENTRY_LABELS):
                return str(entry[index.column()])
        elif role == Qt.BackgroundRole:
            column = index.column()
        return None


@register_binding_controller(
    ui_name='Doocs Device Table',
    klassname='DoocsTable',
    binding_type=VectorHashBinding,
    is_compatible=with_display_type('WidgetNode|DoocsTable'),
    priority=-10, can_show_nothing=True)
class DisplayDoocsTable(BaseBindingController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DoocsManagerTableModel, args=())
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
        self.table_model = DoocsManagerTable(parent=table_view)

        # here we set our model
        table_view.setModel(self.table_model)
        btn_delegate = ButtonDelegate(
            parent=table_view, device_id=self.proxy.root_proxy.device_id)
        table_view.setItemDelegateForColumn(
            MANAGER_SERVER_COLUMN, btn_delegate)
        self.delegate = btn_delegate

        header = table_view.horizontalHeader()
        header.setDefaultSectionSize(50)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents))
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents))

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
