#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on August 26, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QAction, QCompleter
from traits.api import Instance, on_trait_change

from karabogui.api import (
    BaseLineEditController, PropertyProxy, StringBinding, VectorStringBinding,
    get_binding_value, has_options, register_binding_controller)

from .models.api import EditableTextOptionsModel
from .utils import requires_gui_version

requires_gui_version(2, 16)


class OptionValidator(QValidator):

    def __init__(self, strict=False, parent=None):
        super().__init__(parent)
        self._strict = strict
        self._options = []

    def validate(self, input, pos):
        if not self._strict:
            return QValidator.Acceptable, input, pos
        if not self._options:
            return QValidator.Acceptable, input, pos

        for option in self._options:
            if input == option:
                return QValidator.Acceptable, input, pos
            elif option.startswith(input):
                return QValidator.Intermediate, input, pos

        return QValidator.Invalid, input, pos

    def setOptions(self, options):
        self._options = options

    def setStrict(self, strict):
        self._strict = strict


def is_compatible(binding):
    """The StringBinding must be available for the controller"""
    return isinstance(binding, StringBinding) and not has_options(binding)


@register_binding_controller(
    ui_name="Completer Edit (with Options)",
    klassname="EditableTextOptions",
    binding_type=(StringBinding, VectorStringBinding),
    can_edit=True, is_compatible=is_compatible,
    priority=-10, can_show_nothing=False)
class EditableTextOptions(BaseLineEditController):
    """The Editable Options widget

    This line edit can have a dragged vector string for popup completion
    """
    model = Instance(EditableTextOptionsModel, args=())
    completer = Instance(QCompleter)

    # The additional proxy providing the options
    option_proxy = Instance(PropertyProxy)

    def create_widget(self, parent):
        widget = super().create_widget(parent)
        strict_action = QAction("Strict validation", widget)
        strict_action.setCheckable(True)
        strict_action.setChecked(self.model.strict)
        strict_action.triggered.connect(self._change_strict)
        widget.addAction(strict_action)
        return widget

    def add_proxy(self, proxy):
        binding = proxy.binding
        if binding is None:
            self.option_proxy = proxy
            return True

        if not isinstance(binding, VectorStringBinding):
            return False

        if (self.option_proxy is None
                and proxy.root_proxy is self.proxy.root_proxy):
            self.option_proxy = proxy
            return True

        return False

    def remove_proxy(self, proxy):
        if proxy is self.option_proxy:
            self._set_internal_completer([])
            self.validator.setOptions([])
            self.option_proxy = None
            return True

        return False

    def create_validator(self):
        return OptionValidator(strict=self.model.strict)

    def value_update(self, proxy):
        if proxy is self.proxy:
            super().value_update(proxy)
        else:
            value = get_binding_value(proxy.binding, [])
            self._set_internal_completer(value)
            self.validator.setOptions(value)
        self.validate_text_color()

    # -----------------------------------------------------------------------

    def _set_internal_completer(self, value):
        """Internal method to create and set a completer with `value`"""
        self.completer = QCompleter(value, parent=self.widget)
        self.completer.setCaseSensitivity(False)
        self.completer.setCompletionMode(
            QCompleter.PopupCompletion)
        self.internal_widget.setCompleter(self.completer)

    @on_trait_change("model:strict")
    def _strict_change(self):
        self.validator.setStrict(self.model.strict)
        self.value_update(self.proxy)

    # Qt Slots
    # -----------------------------------------------------------------------

    def _change_strict(self, state):
        self.model.strict = state
