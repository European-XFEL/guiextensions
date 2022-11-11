from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QAction, QInputDialog
from traits.api import Instance, on_trait_change

from extensions.models.api import (
    VectorLimitedDoubleLineEditModel, VectorLimitedIntLineEditModel)
from karabogui.api import (
    BaseLineEditController, FloatBinding, IntBinding, IntValidator,
    NumberValidator, PropertyProxy, VectorBinding, VectorDoubleBinding,
    get_binding_value, get_native_min_max, has_min_max_attributes,
    is_vector_integer, register_binding_controller)

MAX_FLOATING_PRECISION = 12


class LimitedValidator(QValidator):
    def __init__(self, validator, parent=None, nativeMin=None, nativeMax=None):
        super().__init__(parent=parent)
        self.validator = validator
        self.minInc = None
        self.maxInc = None
        self.nativeMin = nativeMin
        self.nativeMax = nativeMax

    def setBottom(self, value):
        self.minInc = value
        value = max(self.minInc, self.nativeMin)
        self.validator.setBottom(value)

    def setTop(self, value):
        self.maxInc = value
        value = min(self.maxInc, self.nativeMax)
        self.validator.setTop(value)

    def setNativeMin(self, value):
        if self.minInc is None:
            self.minInc = value
        self.nativeMin = value

    def setNativeMax(self, value):
        if self.maxInc is None:
            self.maxInc = value
        self.nativeMax = value

    def setDecimals(self, value):
        self.validator.decimals = value

    def validate(self, input, pos):
        return self.validator.validate(input, pos)

    def reset_to_native(self):
        self.setBottom(self.nativeMin)
        self.setTop(self.nativeMax)


class VectorLimitedLineEdit(BaseLineEditController):
    range_proxy = Instance(PropertyProxy)

    def add_proxy(self, proxy):
        """
        Allow adding vector proxy of int or double with exactly 2 values- that
        defines min and max of the allowed range.
        """
        if proxy.binding is None:
            self.range_proxy = proxy
            return True
        if self.range_proxy is not None:
            return False
        if self._is_proxy_compatible(proxy) and (proxy.root_proxy is
                                                 self.proxy.root_proxy):
            self.range_proxy = proxy
            return True
        return False

    def remove_proxy(self, proxy):
        if proxy is self.range_proxy:
            self.range_proxy = None
            self.validator.reset_to_native()
            self.validate_text_color()
            return True
        return False

    def value_update(self, proxy):

        if proxy is self.proxy:
            super().value_update(proxy)
        else:
            value = get_binding_value(proxy)
            if value is None:
                return
            min_value = min(value)
            max_value = max(value)
            self.validator.setBottom(min_value)
            self.validator.setTop(max_value)
        self.validate_text_color()

    def _is_proxy_compatible(self, proxy):
        binding = proxy.binding
        if binding.display_type.split("|")[0] != "Range":
            return False
        return self._is_same_vector_type(binding)

    def binding_validator(self, proxy):
        """Reimplemented method of `BaseLineEditController`"""
        if proxy is not self.proxy:
            return
        low, high = get_native_min_max(proxy.binding)
        self.validator.setNativeMin(low)
        self.validator.setNativeMax(high)


def is_compatible(binding):
    return (not has_min_max_attributes(binding) and
            (isinstance(binding, FloatBinding) or
            isinstance(binding, IntBinding))
            )


@register_binding_controller(ui_name="Vector Limited Double Field",
                             klassname="VectorLimitedDoubleLineEdit",
                             binding_type=(FloatBinding, VectorBinding),
                             is_compatible=is_compatible,
                             can_edit=True, priority=0,
                             can_show_nothing=False)
class VectorLimitedDoubleLineEdit(VectorLimitedLineEdit):
    model = Instance(VectorLimitedDoubleLineEditModel, args=())

    def create_widget(self, parent):
        widget = super().create_widget(parent)
        decimal_action = QAction("Change number of decimals", widget)
        decimal_action.triggered.connect(self._pick_decimals)
        widget.addAction(decimal_action)
        return widget

    # ----------------------------------------------------------------------
    # Abstract Interface

    def create_validator(self):
        validator = LimitedValidator(NumberValidator(
            decimals=self.model.decimals))
        return validator

    def toString(self, value):
        """Reimplemented method of `BaseLineEditController`"""
        format_str = ("{}" if self.model.decimals == -1
                      else "{{:.{}f}}".format(self.model.decimals))
        return format_str.format(float(str(value)))

    def fromString(self, value):
        """Reimplemented method of `BaseLineEditController`"""
        return float(value)

    # ----------------------------------------------------------------------

    @on_trait_change("model.decimals", post_init=True)
    def _decimals_update(self):
        self.value_update(self.proxy)
        self.validator.setDecimals(self.model.decimals)

    def _pick_decimals(self, checked):
        num_decimals, ok = QInputDialog.getInt(
            self.widget, "Decimal", "Floating point precision:",
            self.model.decimals, -1, MAX_FLOATING_PRECISION)
        if ok:
            self.model.decimals = num_decimals

    def _is_same_vector_type(self, binding):
        """Check if the proxy binding is Vector double binding"""
        return isinstance(binding, VectorDoubleBinding)


@register_binding_controller(ui_name="Vector Limited Integer Field",
                             klassname="VectorLimitedIntLineEdit",
                             binding_type=(IntBinding, VectorBinding),
                             is_compatible=is_compatible,
                             can_edit=True, priority=0,
                             can_show_nothing=False)
class VectorLimitedIntLineEdit(VectorLimitedLineEdit):
    model = Instance(VectorLimitedIntLineEditModel, args=())

    def create_validator(self):
        validator = LimitedValidator(validator=IntValidator())
        return validator

    def fromString(self, value):
        return int(value)

    def _is_same_vector_type(self, binding):
        """
        Check if the proxy binding is Vector int binding
        """
        return is_vector_integer(binding)
