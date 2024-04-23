from qtpy import uic
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QDialog, QHeaderView

from .utils import get_panel_ui


class SelectionDialog(QDialog):

    def __init__(self, devices, excluded, parent=None):
        super().__init__(parent)
        uic.loadUi(get_panel_ui("exclude_dialog.ui"), self)
        self.setModal(False)

        item_model = QStandardItemModel(parent=self)
        item_model.setHorizontalHeaderLabels(["Select", "Source"])
        self.table_view.setModel(item_model)
        self.table_view.setSelectionBehavior(self.table_view.SelectRows)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        self.select_all.clicked.connect(self.on_select_all)
        self.deselect_all.clicked.connect(self.on_de_select_all)

        root = item_model.invisibleRootItem()
        for source in devices:
            checkbox = QStandardItem()
            checked = Qt.Checked if source not in excluded else Qt.Unchecked
            checkbox.setEditable(False)
            checkbox.setCheckable(True)
            checkbox.setCheckState(checked)
            checkbox.setTextAlignment(Qt.AlignCenter)

            item = QStandardItem(source)
            item.setEditable(False)
            item.setData(source, Qt.UserRole)
            root.appendRow([checkbox, item])

    def _select_items(self, checkstate):
        model = self.table_view.model()
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            item.setCheckState(checkstate)

    @Slot()
    def on_select_all(self):
        self._select_items(Qt.Checked)

    @Slot()
    def on_de_select_all(self):
        self._select_items(Qt.Unchecked)

    @property
    def devices(self):
        h = []
        model = self.table_view.model()
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            if not item.checkState():
                source = model.item(row, 1)
                h.append(source.data(Qt.UserRole))
        return h
