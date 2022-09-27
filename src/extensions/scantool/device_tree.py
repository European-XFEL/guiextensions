import json

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QPushButton, QSizePolicy, QTreeWidget,
    QTreeWidgetItem, QWidget)

import karabogui.icons as icons
from karabogui.itemtypes import NavigationItemTypes, ProjectItemTypes


class ButtonToolbar(QWidget):

    buttonClicked = Signal(str)

    def __init__(self, tree_widget, parent):
        super(ButtonToolbar, self).__init__(parent)

        self.add_button = QPushButton(icons.add, "", self)
        self.add_button.setToolTip("Add new device")
        self.copy_button = QPushButton(icons.editCopy, "", self)
        self.copy_button.setToolTip("Copy device")
        self.up_button = QPushButton(icons.arrowFancyUp, "", self)
        self.up_button.setToolTip("Move selected item up")
        self.up_button.setEnabled(False)
        self.down_button = QPushButton(icons.arrowFancyDown, "", self)
        self.down_button.setToolTip("Move selected item down")
        self.down_button.setEnabled(False)
        self.remove_button = QPushButton(icons.no, "", self)
        self.remove_button.setToolTip("Remove selected item")
        self.remove_button.setEnabled(False)
        self.remove_all_button = QPushButton(icons.delete, "", self)
        self.remove_all_button.setToolTip("Remove all items")
        self.sort_button = QPushButton(icons.reset, "", self)
        self.sort_button.setToolTip("Sort items by active")
        self.apply_button = QPushButton(icons.yes, "Apply", self)
        self.apply_button.setToolTip("Apply changes")
        self.apply_button.setEnabled(False)

        hlayout = QHBoxLayout(self)
        hlayout.addWidget(self.add_button)
        hlayout.addWidget(self.sort_button)
        hlayout.addWidget(self.copy_button)
        hlayout.addWidget(self.up_button)
        hlayout.addWidget(self.down_button)
        hlayout.addWidget(self.remove_button)
        hlayout.addWidget(self.remove_all_button)
        hlayout.addStretch(10)
        hlayout.addWidget(self.apply_button)
        hlayout.setContentsMargins(0, 0, 0, 0)

        self.add_button.clicked.connect(self._add_clicked)
        self.copy_button.clicked.connect(self._copy_clicked)
        self.up_button.clicked.connect(self._up_clicked)
        self.down_button.clicked.connect(self._down_clicked)
        self.remove_button.clicked.connect(self._remove_clicked)
        self.sort_button.clicked.connect(self._sort_clicked)
        self.remove_all_button.clicked.connect(self._remove_all_clicked)
        self.apply_button.clicked.connect(self._apply_clicked)

        self.tree_widget = tree_widget
        self.tree_widget.itemSelectionChanged.connect(
            self._item_selection_changed)

    def _add_clicked(self):
        self.buttonClicked.emit("add")

    def _copy_clicked(self):
        item = self.tree_widget.currentItem()
        parent = item.parent()
        index = parent.indexOfChild(item)
        new_item = item.clone()
        parent.insertChild(index + 1, new_item)
        self.tree_widget.setCurrentItem(new_item)
        self.set_apply_button_enabled(True)

    def _up_clicked(self):
        self.move_current_item(-1)

    def _down_clicked(self):
        self.move_current_item(1)

    def move_current_item(self, direction):
        item = self.tree_widget.currentItem()
        parent = item.parent()
        index = parent.indexOfChild(item)
        parent.takeChild(index)
        parent.insertChild(index + direction, item)
        self.tree_widget.setCurrentItem(item)
        self.set_apply_button_enabled(True)

    def _remove_clicked(self):
        item = self.tree_widget.currentItem()
        parent = item.parent()
        parent.removeChild(item)
        self.set_apply_button_enabled(True)
        self.set_button_states()

    def _sort_clicked(self):
        self.buttonClicked.emit("sort")

    def _remove_all_clicked(self):
        self.buttonClicked.emit("remove_all")
        self.set_apply_button_enabled(True)
        self.set_button_states()

    def _apply_clicked(self):
        self.buttonClicked.emit("apply")

    def _item_added(self):
        self.set_apply_button_enabled(True)

    def _item_selection_changed(self):
        self.set_button_states()

    def set_button_states(self):
        item = self.tree_widget.currentItem()
        if item is None:
            # Case when child item has been deleted
            is_child_item = False
        else:
            is_child_item = self.tree_widget.indexOfTopLevelItem(item) == -1
        self.copy_button.setEnabled(is_child_item)
        self.remove_button.setEnabled(is_child_item)
        if is_child_item:
            index = item.parent().indexOfChild(item)
            self.up_button.setEnabled(index > 0)
            self.down_button.setEnabled(index < item.parent().childCount() - 1)
        else:
            self.up_button.setEnabled(False)
            self.down_button.setEnabled(False)

    def set_apply_button_enabled(self, state):
        self.apply_button.setEnabled(state)


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
        self.setExpandsOnDoubleClick(False)

    def dragEnterEvent(self, event):
        self._check_drag_event(event)

    def dragMoveEvent(self, event):
        self._check_drag_event(event)

    def dropEvent(self, event):
        success, data = self._check_drag_event(event)
        drop_item, device_id = data

        if success:
            parent = drop_item.parent()
            if parent is None:
                # Item droped on the top level item. Add new child item
                alias = device_id.split("/")[-1]
                key = ""
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
                self.setCurrentItem(drop_item)
                self.itemChanged.emit(drop_item, 1)

    def _check_drag_event(self, event):
        """Check the drag event for enter, drag, and drop events.

        This method returns a success boolean and a tuple of meta data when
        successful (drop_item: QTreeWidgetItem, device_id: str)
        """
        items = event.mimeData().data('treeItems').data()
        if not items:
            event.ignore()
            return False, ()

        # Check if a device was dragged in the item
        item = json.loads(items.decode())[0]
        item_type = item.get('type')
        from_navigation = item_type == NavigationItemTypes.DEVICE
        from_project = item_type == ProjectItemTypes.DEVICE
        from_device = from_navigation or from_project

        drop_item = self.itemAt(event.pos())
        if from_device and drop_item is not None:
            event.accept()
            device_id = item.get('deviceId', 'None')
            return True, (drop_item, device_id)
        else:
            event.ignore()
            return False, ()
