#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
import json
from enum import Enum

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QPushButton, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from traits.api import Bool, Instance

from karabo.native import Hash
from karabogui.api import (
    BaseBindingController, SignalBlocker, VectorHashBinding, get_binding_value,
    icons, is_proxy_allowed, make_brush, register_binding_controller,
    with_display_type)
from karabogui.itemtypes import (
    ConfiguratorItemType, NavigationItemTypes, ProjectItemTypes)

from ..models.api import EventConfigurationModel
from ..utils import OptionsDelegate

EVENT_ATTRIBUTES = ["alias", "level", "condition"]
GRAY = QColor(178, 178, 178, 60)


class EventColorMap(Enum):
    CRITICAL = make_brush("r")
    IMPORTANT = make_brush("y")
    EVENT = make_brush("s")


class EventTreeWidget(QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setUniformRowHeights(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setUniformRowHeights(True)
        self.setExpandsOnDoubleClick(True)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)

        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.header().setSectionResizeMode(QHeaderView.Interactive)
        self.setColumnCount(len(EVENT_ATTRIBUTES))
        self.setHeaderLabels([attr.title() for attr in EVENT_ATTRIBUTES])

        options = [cond_type.name for cond_type in EventColorMap]
        delegate = OptionsDelegate(options, parent=self)
        self.setItemDelegateForColumn(1, delegate)

    def refresh(self, events):
        """Update event conditions tree

        Args:
            events (list): list of dictionaries describing events
        """
        self.clear()
        # TODO preserve selected item

        if not events:
            return

        for event in events:
            self.add_tree_item(event=event)

    def add_tree_item(self, event, level_item=None, parent=None):
        if parent is None:
            # Try to find top level item
            for idx in range(self.topLevelItemCount()):
                if self.topLevelItem(idx).text(0) == event["alias"]:
                    parent = self.topLevelItem(idx)

        item_to_select = None
        if parent is None:
            parent = QTreeWidgetItem([event["alias"]])
            parent.setFlags(parent.flags() ^ Qt.ItemIsEditable)
            self.addTopLevelItem(parent)
            item_to_select = parent

        if level_item is None:
            level_item = QTreeWidgetItem(["", event["level"], ""])
            level_item.setFlags(level_item.flags() ^ Qt.ItemIsEditable)
            level_item.setBackground(
                1, getattr(EventColorMap, event["level"]).value)
            parent.addChild(level_item)
            if not item_to_select:
                item_to_select = level_item

        for idx, cond in enumerate(event["condition"]):
            cond_item = QTreeWidgetItem(["", "", cond])
            cond_item.setFlags(cond_item.flags() ^ Qt.ItemIsEditable)
            level_item.addChild(cond_item)
            brush = QBrush(GRAY) if idx % 2 else QBrush(Qt.white)
            cond_item.setBackground(2, brush)
            if not item_to_select:
                item_to_select = cond_item

        # Sort level items by critical level
        last_index = 0
        for event_level in EventColorMap:
            for idx in range(parent.childCount()):
                if parent.child(idx).text(1) == event_level.name:
                    item = parent.takeChild(idx)
                    parent.insertChild(last_index, item)
                    last_index += 1

        # Expand event branch
        parent.setExpanded(True)
        for idx in range(parent.childCount()):
            parent.child(idx).setExpanded(True)
        self.setCurrentItem(item_to_select)

    def mouseDoubleClickEvent(self, event):
        # Do not allow to edit items without text
        index = self.indexAt(event.pos())
        text = index.data(Qt.DisplayRole)
        if text:
            event.accept()
            return super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        self._check_drag_event(event)

    def dragMoveEvent(self, event):
        self._check_drag_event(event)

    def dropEvent(self, event):
        success, data = self._check_drag_event(event)
        if success:
            drop_pos_item, key = data
            alias = "NEW_EVENT"
            level = EventColorMap.IMPORTANT.name

            level_item = None
            parent_item = None

            if drop_pos_item is not None:
                if drop_pos_item.parent() is None:
                    # Top level item
                    parent_item = drop_pos_item
                    alias = drop_pos_item.text(0)
                else:
                    if drop_pos_item.childCount() == 0:
                        # Condition item
                        level_item = drop_pos_item.parent()
                    else:
                        level_item = drop_pos_item

                    parent_item = level_item.parent()
                    alias = parent_item.text(0)
                    level = level_item.text(1)

            event_item = {"alias": alias,
                          "level": level,
                          "condition": [key]}
            self.add_tree_item(event=event_item, level=level_item,
                               parent=parent_item)

    def _check_drag_event(self, event):
        """Check the drag event for enter, drag, and drop events.

        This method returns a success boolean and a tuple of meta data when
        successful (drop_item: QTreeWidgetItem, device_id or key: str)
        """

        # Check if a device attribute is dragged
        items = event.mimeData().data("tree_items").data()
        if items:
            item = json.loads(items.decode())[0]
            item_type = item.get("type")

            if item_type == ConfiguratorItemType.LEAF:
                drop_item = self.itemAt(event.pos())
                key = item.get("key")
                event.accept()
                return True, (drop_item, f"krb:{key}")

        # Check if the device id is dragged
        items = event.mimeData().data("treeItems").data()
        if items:
            item = json.loads(items.decode())[0]
            item_type = item.get("type")
            from_navigation = item_type == NavigationItemTypes.DEVICE
            from_project = item_type == ProjectItemTypes.DEVICE
            from_device = from_navigation or from_project

            drop_item = self.itemAt(event.pos())
            if from_device:
                device_id = item.get("deviceId", "None")
                event.accept()
                return True, (drop_item, f"krb_offline:{device_id}")

        event.ignore()
        return False, ()


class ButtonToolbar(QWidget):

    buttonClicked = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)

        self.add_bt = QPushButton(icons.add, "", self)
        self.add_bt.setToolTip("Add new item")
        self.copy_bt = QPushButton(icons.editCopy, "", self)
        self.copy_bt.setToolTip("Copy item")
        self.remove_bt = QPushButton(icons.no, "", self)
        self.remove_bt.setToolTip("Remove selected item")
        self.remove_bt.setEnabled(False)
        self.remove_all_bt = QPushButton(icons.delete, "", self)
        self.remove_all_bt.setToolTip("Remove all items")

        self.buttons = {self.add_bt: "add",
                        self.copy_bt: "copy",
                        self.remove_bt: "remove",
                        self.remove_all_bt: "remove_all"}

        hlayout = QHBoxLayout(self)
        for widget in self.buttons.keys():
            hlayout.addWidget(widget)
            widget.clicked.connect(self._button_clicked)
        hlayout.addStretch(10)
        hlayout.setContentsMargins(0, 0, 0, 0)

    def _button_clicked(self):
        self.buttonClicked.emit(self.buttons[self.sender()])

    def set_button_state(self, selected_items):
        self.copy_bt.setEnabled(len(selected_items) > 0)
        self.remove_bt.setEnabled(len(selected_items) > 0)


class EventConfigurationWidget(QWidget):

    eventTreeChanged = Signal()

    def __init__(self, parent):
        super().__init__(parent)

        self._event_tree = EventTreeWidget(parent=self)
        self._toolbar = ButtonToolbar(parent=self)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._toolbar)
        main_layout.addWidget(self._event_tree)

        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)
        self._event_tree.itemChanged.connect(
            self._event_item_changed)
        self._event_tree.itemSelectionChanged.connect(
            self._event_selection_changed)
        self._toolbar.buttonClicked.connect(self._toolbar_button_clicked)

    def update_event_tree(self, events):
        with SignalBlocker(self._event_tree):
            self._event_tree.refresh(events)

    def _event_item_changed(self, item, col):
        if col == 1:
            item.setBackground(1, getattr(EventColorMap, item.text(1)).value)
        self.eventTreeChanged.emit()

    def _event_selection_changed(self):
        selected_items = self._event_tree.selectedItems()
        self._toolbar.set_button_state(selected_items)

    def _toolbar_button_clicked(self, button):
        item = self._event_tree.currentItem()
        parent = item.parent() if item else None

        if button == "add":
            level_item = None
            event = {"alias": "NEW_EVENT",
                     "level": EventColorMap.IMPORTANT.name,
                     "condition": ["NEW_CONDITION"]}
            # Level or conditions item is selected
            if item and parent:
                event["alias"] = ""
                if item.childCount() == 0:
                    level_item = parent
                    parent = level_item.parent()
                    event["level"] = level_item.text(1)
                else:
                    event["level"] = EventColorMap.IMPORTANT.name
            self._event_tree.add_tree_item(event, level_item, parent)
        elif button == "copy":
            new_item = item.clone()
            if parent is None:
                index = self._event_tree.indexOfTopLevelItem(item)
                self._event_tree.insertTopLevelItem(index + 1, new_item)
            else:
                index = parent.indexOfChild(item)
                parent.insertChild(index + 1, new_item)
            new_item.setExpanded(True)
            self._event_tree.setCurrentItem(new_item)
        elif button == "remove":
            if parent is None:
                index = self._event_tree.indexOfTopLevelItem(item)
                self._event_tree.takeTopLevelItem(index)
            else:
                parent.removeChild(item)
        elif button == "remove_all":
            self._event_tree.clear()
        self.eventTreeChanged.emit()

    def get_event_config(self):
        result = []
        for p_idx in range(self._event_tree.topLevelItemCount()):
            parent_item = self._event_tree.topLevelItem(p_idx)
            for l_idx in range(parent_item.childCount()):
                level_item = parent_item.child(l_idx)
                h = Hash("alias", parent_item.text(0),
                         "level", level_item.text(1))
                conditions = [level_item.child(idx).text(2)
                              for idx in range(level_item.childCount())]
                h["condition"] = conditions
                result.append(h)
        return result


@register_binding_controller(
    ui_name="Event Condition View",
    klassname="EventConfigurationView",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("EventConfigurationView"),
    can_edit=True, can_show_nothing=True)
class EventConfigurationView(BaseBindingController):
    model = Instance(EventConfigurationModel, args=())

    # Implement own custom menu
    _is_editing = Bool(False)
    _is_updating = Bool(False)

    def create_widget(self, parent):
        main_widget = EventConfigurationWidget(parent=parent)
        main_widget.eventTreeChanged.connect(self._event_tree_changed)
        return main_widget

    def value_update(self, proxy):
        if self._is_editing:
            return

        self._is_updating = True
        events = get_binding_value(proxy)
        self.widget.update_event_tree(events)
        self._is_updating = False

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)

    def _event_tree_changed(self):
        if self.proxy.binding is None or self._is_updating:
            return

        self._is_editing = True
        self.proxy.edit_value = self.widget.get_event_config()
        self._is_editing = False
