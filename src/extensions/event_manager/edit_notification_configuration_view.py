#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
from enum import Enum, IntEnum

from qtpy.QtCore import QModelIndex, QRegExp, Qt, Signal
from qtpy.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QListWidget, QListWidgetItem, QSplitter,
    QToolButton, QVBoxLayout, QWidget)
from traits.api import Instance, WeakRef

from karabogui.api import (
    BaseFilterTableController, KaraboTableView, SignalBlocker,
    VectorHashBinding, get_binding_value, icons, register_binding_controller,
    with_display_type)

from ..models.api import NotificationConfigurationTableModel
from ..utils import VectorDelegate


class Targets(IntEnum):
    emailAddresses = 3
    phoneNumbers = 4
    zulipTopics = 5


class DeviceAction(Enum):
    ADD = "add"
    REMOVE = "remove"
    RENAME = "rename"


class DeviceIdsWidget(QWidget):

    deviceIdChanged = Signal(DeviceAction, list)
    selectedDeviceIdChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.device_ids_lwidget = QListWidget(parent=parent)
        self.device_ids_lwidget.setSelectionMode(
            QAbstractItemView.SingleSelection)
        self.device_ids_lwidget.currentTextChanged.connect(
            self._current_device_id_changed)
        self.device_ids_lwidget.itemChanged.connect(self._item_changed)
        self.current_device_id = None

        button_toolbar = QWidget(parent)
        self.add_button = QToolButton(button_toolbar)
        self.add_button.setIcon(icons.add)
        self.add_button.setToolTip("Add")
        self.remove_button = QToolButton(button_toolbar)
        self.remove_button.setIcon(icons.no)
        self.remove_button.setToolTip("Remove")

        bt_hlayout = QHBoxLayout(button_toolbar)
        bt_hlayout.setContentsMargins(0, 0, 0, 0)
        bt_hlayout.addStretch()
        bt_hlayout.addWidget(self.add_button)
        bt_hlayout.addWidget(self.remove_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.device_ids_lwidget)
        main_layout.addWidget(button_toolbar)

        self.add_button.clicked.connect(self.add_new_item)
        self.remove_button.clicked.connect(self.remove_item)

        self.setMaximumWidth(250)

    def update_device_ids(self, device_ids):
        current_items = set([self.device_ids_lwidget.item(x).text()
                             for x in range(self.device_ids_lwidget.count())])
        if current_items == device_ids:
            return

        with SignalBlocker(self.device_ids_lwidget):
            self.device_ids_lwidget.clear()
            for dev_id in device_ids:
                item = QListWidgetItem(dev_id)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.device_ids_lwidget.addItem(item)
        if self.current_device_id in device_ids:
            self.device_ids_lwidget.setCurrentRow(
                device_ids.index(self.current_device_id))
        else:
            self.device_ids_lwidget.setCurrentRow(0)

    def _current_device_id_changed(self, device_id):
        self.current_device_id = device_id
        self.selectedDeviceIdChanged.emit(device_id)

    def _item_changed(self, item):
        self.deviceIdChanged.emit(DeviceAction.RENAME,
                                  [self.current_device_id, item.text()])

    def add_new_item(self):
        item = QListWidgetItem("DEVICE_ID")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.device_ids_lwidget.addItem(item)
        self.deviceIdChanged.emit(DeviceAction.ADD, [item.text()])
        self.device_ids_lwidget.setCurrentItem(item)

    def remove_item(self):
        device_id = self.device_ids_lwidget.currentItem().text()
        self.device_ids_lwidget.takeItem(self.device_ids_lwidget.currentRow())
        self.deviceIdChanged.emit(DeviceAction.REMOVE, [device_id])


@register_binding_controller(
    ui_name="Notification Configuration View",
    klassname="NotificationConfigurationView",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("NotificationConfigurationView"),
    can_edit=True, can_show_nothing=True)
class NotificationConfigurationView(BaseFilterTableController):
    model = Instance(NotificationConfigurationTableModel, args=())

    _device_ids_widget = WeakRef(DeviceIdsWidget)

    def create_widget(self, parent):
        main_widget = QSplitter(parent)
        table_widget = super().create_widget(parent)
        for child in table_widget.children():
            if not isinstance(child, (KaraboTableView, QVBoxLayout)):
                child.setHidden(True)
        self.model.filterKeyColumn = 0

        device_ids_widget = DeviceIdsWidget(parent)
        device_ids_widget.deviceIdChanged.connect(self._device_id_changed)
        device_ids_widget.selectedDeviceIdChanged.connect(
            self._selected_device_id_changed)
        main_layout = QHBoxLayout(main_widget)
        main_layout.addWidget(device_ids_widget)
        main_layout.addWidget(table_widget)

        self._device_ids_widget = device_ids_widget

        return main_widget

    def create_delegates(self):
        for target in Targets:
            delegate = VectorDelegate(self.proxy, col=target.name,
                                      parent=self.tableWidget())
            self.tableWidget().setItemDelegateForColumn(target.value,
                                                        delegate)

    def value_update(self, proxy):
        super().value_update(proxy)
        data = get_binding_value(proxy, [])
        device_ids = list(set(row["eventManagerId"] for row in data))
        self._device_ids_widget.update_device_ids(device_ids)
        self.tableWidget().setColumnHidden(0, True)

    def _device_id_changed(self, action, device_ids):
        model = self.sourceModel()
        if action == DeviceAction.ADD:
            model.add_row_below(model.rowCount() - 1)
            index = model.index(model.rowCount() - 1, 0, QModelIndex())
            model.setData(index, device_ids[0])
        elif action == DeviceAction.REMOVE:
            pass
        elif action == DeviceAction.RENAME:
            old_device_id, new_device_ids = device_ids
            for row in range(model.rowCount()):
                index = model.index(row, 0, QModelIndex())
                if model.data(index) == old_device_id:
                    model.setData(index, new_device_ids)
                    break
            self._selected_device_id_changed(new_device_ids)

    def _selected_device_id_changed(self, device_id):
        # TODO hide all rows if None passed
        self.tableWidget().model().setFilterRegExp(
            QRegExp(f"^{device_id}$", Qt.CaseInsensitive))
