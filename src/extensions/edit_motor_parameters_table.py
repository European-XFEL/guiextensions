#############################################################################
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtWidgets import QMenu
from traits.api import Bool, Instance, List, String, WeakRef

from karabogui.api import (
    BaseFilterTableController, PropertyProxy, VectorHashBinding,
    get_binding_value, register_binding_controller, with_display_type)

from .models.api import MotorParametersTableModel


@register_binding_controller(
    ui_name="Motor Parameters Table",
    klassname="MotorParametersTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("MotorParametersTable"),
    can_edit=True, priority=-10, can_show_nothing=True)
class EditableMotorParametersTable(BaseFilterTableController):
    model = Instance(MotorParametersTableModel, args=())

    hasCustomMenu = Bool(True)
    class_menu = WeakRef(QMenu)
    class_names = List(String)
    device_classes_proxy = Instance(PropertyProxy)

    def create_widget(self, parent):
        widget = super().create_widget(parent)
        self.device_classes_proxy = PropertyProxy(
            root_proxy=self.proxy.root_proxy, path="deviceClasses")
        self.class_names = get_binding_value(self.device_classes_proxy, [])
        return widget

    def custom_menu(self, pos):
        """Subclassed method for own custom menu

        :param: pos: The position of the context menu event
        """
        index = self.tableWidget().indexAt(pos)
        if index.isValid() and index.column() == 4:
            menu = self.get_available_classes_menu()
        else:
            menu = self.get_basic_menu()
        menu.exec_(self.tableWidget().viewport().mapToGlobal(pos))

    def get_available_classes_menu(self):
        self.class_names = get_binding_value(self.device_classes_proxy, [])
        self.class_menu = QMenu(parent=self.tableWidget())
        index = self.currentIndex()
        model = index.model()
        for class_name in self.class_names:
            action = self.class_menu.addAction(class_name)
            action.setCheckable(True)
            _, selected_classes = model.get_model_data(index.row(), 4)
            action.setChecked(class_name in selected_classes)
            action.triggered.connect(self.action_class_selected)
        return self.class_menu

    def action_class_selected(self):
        model = self.sourceModel()
        actions = self.class_menu.actions()
        selected_classes = [act.text() for act in actions if act.isChecked()]
        model.setData(self.currentIndex(), ",".join(selected_classes))
