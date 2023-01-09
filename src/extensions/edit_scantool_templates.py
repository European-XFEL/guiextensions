#############################################################################
# Author: Ivars Karpics
# Created July 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################


from qtpy.QtCore import QStringListModel
from qtpy.QtWidgets import (
    QComboBox, QCompleter, QHBoxLayout, QToolButton, QWidget)
from traits.api import Instance, List, String, WeakRef

from karabo.common.api import WeakMethodRef
from karabogui.api import (
    BaseBindingController, SignalBlocker, VectorHashBinding, call_device_slot,
    get_binding_value, get_reason_parts, icons, is_proxy_allowed, messagebox,
    register_binding_controller, with_display_type)

from .models.api import ScantoolTemplatesModel


@register_binding_controller(
    ui_name="Scantool Templates",
    klassname="ScantoolTemplates",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("ScantoolTemplates"),
    can_show_nothing=True, can_edit=True)
class ScantoolTemplates(BaseBindingController):
    # The scene model class used by this controller
    model = Instance(ScantoolTemplatesModel, args=())
    # Private traits
    completer = Instance(QCompleter)
    template_names = List(String)
    template_timestamps = List(String)
    templates_cbox = WeakRef(QComboBox)
    add_button = WeakRef(QToolButton)
    remove_button = WeakRef(QToolButton)
    load_button = WeakRef(QToolButton)

    def create_widget(self, parent):
        widget = QWidget(parent=parent)
        self.templates_cbox = QComboBox(widget)
        self.templates_cbox.setEditable(True)
        self.add_button = QToolButton(widget)
        self.add_button.setIcon(icons.add)
        self.add_button.setToolTip("Add new scan template")
        self.remove_button = QToolButton(widget)
        self.remove_button.setIcon(icons.no)
        self.remove_button.setToolTip("Remove selected template")
        self.load_button = QToolButton(widget)
        self.load_button.setText("Load")

        self.completer = QCompleter(self.template_names, parent=self.widget)
        self.completer.setCaseSensitivity(False)
        self.completer.setCompletionMode(
            QCompleter.PopupCompletion)
        self.templates_cbox.setCompleter(self.completer)

        self.templates_cbox.currentTextChanged.connect(
            self.template_name_changed)
        self.add_button.clicked.connect(self.add_template)
        self.remove_button.clicked.connect(self.remove_template)
        self.load_button.clicked.connect(self.load_template)

        main_hlayout = QHBoxLayout(widget)
        main_hlayout.addWidget(self.templates_cbox)
        main_hlayout.addWidget(self.add_button)
        main_hlayout.addWidget(self.remove_button)
        main_hlayout.addWidget(self.load_button)

        return widget

    def value_update(self, proxy):
        templates = get_binding_value(proxy, [])
        self.template_names = [t["name"] for t in templates]
        self.template_timestamps = [t["timestamp"] for t in templates]

        with SignalBlocker(self.templates_cbox):
            self.completer.setModel(
                QStringListModel(self.template_names, self.completer))
            self.templates_cbox.clear()
            self.templates_cbox.addItems(self.template_names)
            self.templates_cbox.setCurrentIndex(
                self.templates_cbox.count() - 1)

        self.remove_button.setEnabled(self.templates_cbox.count() > 0)
        self.load_button.setEnabled(self.templates_cbox.count() > 0)

    def state_update(self, proxy):
        enable = is_proxy_allowed(proxy)
        self.widget.setEnabled(enable)

    def template_name_changed(self, text):
        self.add_button.setEnabled(len(text) > 0)
        self.remove_button.setEnabled(text in self.template_names)
        self.load_button.setEnabled(text in self.template_names)

    def add_template(self):
        call_device_slot(WeakMethodRef(self.handle_request),
                         self.getInstanceId(), "requestAction",
                         name=self.templates_cbox.currentText(),
                         action="addTemplate")

    def remove_template(self):
        call_device_slot(WeakMethodRef(self.handle_request),
                         self.getInstanceId(), "requestAction",
                         name=self.templates_cbox.currentText(),
                         action="removeTemplate")

    def load_template(self, index):
        call_device_slot(WeakMethodRef(self.handle_request),
                         self.getInstanceId(), "requestAction",
                         name=self.templates_cbox.currentText(),
                         action="loadTemplate")

    def handle_request(self, success, reply):
        if not success:
            reason, details = get_reason_parts(reply)
            messagebox.show_error("Error while executing template action: "
                                  f"{reason}", details=details,
                                  parent=self.widget)
