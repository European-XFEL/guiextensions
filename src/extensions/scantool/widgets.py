import json

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QAbstractItemView, QGridLayout, QHBoxLayout, QPushButton, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

import karabogui.icons as icons
from karabogui.itemtypes import (
    ConfiguratorItemType, NavigationItemTypes, ProjectItemTypes)


def get_container(parent, layout=None):
    if layout is None:
        layout = QVBoxLayout()
    widget = ContainerWidget(parent)
    widget.setLayout(layout)
    return widget


class ContainerWidget(QWidget):

    def __init__(self, parent=None):
        super(ContainerWidget, self).__init__(parent)

    # -----------------------------------------------------------------------
    # Public methods

    def add_widget(self, widget, **coords):
        layout = self.layout()
        if layout is None:
            return

        if isinstance(layout, QGridLayout):
            row, col = coords["row"], coords["col"] if coords else (0, 0)
            layout.addWidget(widget, row, col)
        else:
            layout.addWidget(widget)

    def remove_widget(self, widget):
        self.layout().removeWidget(widget)


class ButtonToolbar(QWidget):

    buttonClicked = Signal(str)

    def __init__(self, parent):
        super(ButtonToolbar, self).__init__(parent)

        self.device_dialog_button = QPushButton(icons.zoom, "", self)
        self.device_dialog_button.setToolTip("Device view dialog")
        self.add_button = QPushButton(icons.add, "", self)
        self.add_button.setToolTip("Add device")
        self.copy_button = QPushButton(icons.editCopy, "", self)
        self.copy_button.setToolTip("Copy device")
        self.up_button = QPushButton(icons.arrowFancyUp, "", self)
        self.up_button.setToolTip("Move selected item up")
        self.up_button.setEnabled(False)
        self.down_button = QPushButton(icons.arrowFancyDown, "", self)
        self.down_button.setToolTip("Move selected item down")
        self.down_button.setEnabled(False)
        self.sort_button = QPushButton(icons.reset, "", self)
        self.sort_button.setToolTip("Sort items by active")
        self.remove_button = QPushButton(icons.no, "", self)
        self.remove_button.setToolTip("Remove selected item")
        self.remove_button.setEnabled(False)
        self.remove_all_button = QPushButton(icons.delete, "", self)
        self.remove_all_button.setToolTip("Remove all items")

        self.buttons = {self.device_dialog_button: "device_dialog",
                        self.add_button: "add",
                        self.copy_button: "copy",
                        self.up_button: "up",
                        self.down_button: "down",
                        self.sort_button: "sort",
                        self.remove_button: "remove",
                        self.remove_all_button: "remove_all"}

        hlayout = QHBoxLayout(self)
        for widget in self.buttons.keys():
            hlayout.addWidget(widget)
            widget.clicked.connect(self._button_clicked)
        hlayout.addStretch(10)
        hlayout.setContentsMargins(0, 0, 0, 0)

    def _button_clicked(self):
        self.buttonClicked.emit(self.buttons[self.sender()])

    def update_button_states(self, tree_item):
        is_child_item = False
        if tree_item:
            if tree_item.parent():
                is_child_item = True
        self.copy_button.setEnabled(is_child_item)
        self.remove_button.setEnabled(is_child_item)
        if is_child_item:
            index = tree_item.parent().indexOfChild(tree_item)
            self.up_button.setEnabled(index > 0)
            self.down_button.setEnabled(
                index < tree_item.parent().childCount() - 1)
        else:
            self.up_button.setEnabled(False)
            self.down_button.setEnabled(False)


class DeviceTreeWidget(QTreeWidget):

    def __init__(self, parent=None):
        super(DeviceTreeWidget, self).__init__(parent)

        self.setUniformRowHeights(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)

        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setExpandsOnDoubleClick(True)

    def dragEnterEvent(self, event):
        self._check_drag_event(event)

    def dragMoveEvent(self, event):
        self._check_drag_event(event)

    def dropEvent(self, event):
        success, data = self._check_drag_event(event)
        drop_item, device_id, key = data

        if success:
            parent = drop_item.parent()
            if parent is None:
                # Item droped on the top level item. Add new child item
                alias = device_id.split("/")[-1]
                if not key:
                    if drop_item.text(0) == "Motors":
                        key = "default"
                    elif drop_item.text(0) == "Sources":
                        key = "value"
                new_item = QTreeWidgetItem([alias, device_id, key])
                new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
                new_item.setCheckState(0, Qt.Unchecked)
                drop_item.addChild(new_item)
                self.setCurrentItem(new_item)
                self.itemChanged.emit(new_item, 0)
            else:
                # Item droped on the child. Change deviceId
                drop_item.setText(1, device_id)
                if key:
                    drop_item.setText(2, key)
                self.setCurrentItem(drop_item)
                self.itemChanged.emit(drop_item, 1)

    def _check_drag_event(self, event):
        """Check the drag event for enter, drag, and drop events.

        This method returns a success boolean and a tuple of meta data when
        successful (drop_item: QTreeWidgetItem, device_id: str)
        """
        items = event.mimeData().data("treeItems").data()
        drop_item = self.itemAt(event.pos())
        if not items:
            items = event.mimeData().data("tree_items").data()
        if not items or not drop_item:
            event.ignore()
            return False, ()

        item = json.loads(items.decode())[0]
        item_type = item.get("type")
        # Check if device id is dragged
        if item_type in [NavigationItemTypes.DEVICE, ProjectItemTypes.DEVICE]:
            device_id = item.get("deviceId")
            event.accept()
            return True, (drop_item, device_id, "")
        # Check if a device attribute is dragged
        elif item_type == ConfiguratorItemType.LEAF:
            parts = item.get("key").split(".")
            device_id = parts[0]
            key = ".".join(parts[1:])
            event.accept()
            return True, (drop_item, device_id, key)
        else:
            event.ignore()
            return False, ()
