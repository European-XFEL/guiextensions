from qtpy.QtGui import QValidator

from extensions.edit_limited_lineedit import (
    LimitedValidator, VectorLimitedDoubleLineEdit, VectorLimitedIntLineEdit)
from extensions.models.api import (
    VectorLimitedDoubleLineEditModel, VectorLimitedIntLineEditModel)
from karabo.common.states import State
from karabo.native import (
    Configurable, Double, Int32, String, VectorDouble, VectorInt32)
from karabogui.api import (
    DeviceProxy, IntValidator, NumberValidator, PropertyProxy, build_binding)
from karabogui.conftest import gui_app
from karabogui.testing import get_class_property_proxy, set_proxy_value


class Object(Configurable):
    state = String(defaultValue=State.INIT)
    int_prop = Int32(minInc=-10, maxInc=10, allowedStates=[State.INIT],
                     defaultValue=4)
    double_prop = Double(allowedStates=[State.INIT], defaultValue=3.2)
    invalid_vector_int = VectorInt32()
    vector_int = VectorInt32(displayType="Range")
    vector_double = VectorDouble(displayType="Range")


def test_int_line_edit(gui_app: gui_app):
    schema = Object.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="int_prop")

    controller = VectorLimitedIntLineEdit(
        proxy=proxy, model=VectorLimitedIntLineEditModel())
    controller.create(None)

    int_range_proxy = PropertyProxy(root_proxy=root_proxy, path="vector_int")
    assert int_range_proxy.binding
    set_proxy_value(int_range_proxy, "vector_int", [1, 10])
    double_range_proxy = PropertyProxy(root_proxy=root_proxy,
                                       path="vector_double")
    invalid_range_proxy = get_class_property_proxy(schema,
                                                   "invalid_vector_int")
    controller.set_read_only(False)

    # Doesn't accept VectorDouble
    assert not controller.visualize_additional_property(double_range_proxy)
    # Doesn't accept VectorInt without correct 'displayType'.
    assert not controller.visualize_additional_property(invalid_range_proxy)
    # Accept VectorInt
    assert controller.visualize_additional_property(int_range_proxy)
    # Allow additional proxy only once.
    assert not controller.visualize_additional_property(int_range_proxy)

    controller.value_update(int_range_proxy)

    # Value in the allowed range
    controller.internal_widget.setText("6")

    assert controller.internal_widget.text() == "6"
    assert controller.proxy.edit_value == 6
    assert "color: black" in controller.internal_widget.styleSheet()
    # Value not in the allowed range
    controller.internal_widget.setText("20")

    assert controller.internal_widget.text() == "20"
    assert controller.proxy.edit_value is None
    assert "color: red" in controller.internal_widget.styleSheet()

    # Again value in the allowed range
    controller.internal_widget.setText("5")
    assert controller.internal_widget.text() == "5"
    assert "color: black" in controller.internal_widget.styleSheet()

    # Change range_proxy value to make the value in the allowed range
    controller.internal_widget.setText("20")
    assert "color: red" in controller.internal_widget.styleSheet()
    set_proxy_value(int_range_proxy, "vector_int", [1, 25])
    assert "color: black" in controller.internal_widget.styleSheet()

    # State change
    set_proxy_value(proxy, "state", "CHANGING")
    assert not controller.internal_widget.isEnabled()
    set_proxy_value(proxy, "state", "INIT")
    assert controller.internal_widget.isEnabled()
    set_proxy_value(proxy, "state", "CHANGING")
    assert not controller.internal_widget.isEnabled()


def test_double_line_edit(gui_app: gui_app):
    schema = Object.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="double_prop")
    controller = VectorLimitedDoubleLineEdit(
        proxy=proxy, model=VectorLimitedDoubleLineEditModel())
    controller.create(None)
    int_range_proxy = PropertyProxy(root_proxy=root_proxy, path="vector_int")
    double_range_proxy = PropertyProxy(root_proxy=root_proxy,
                                       path="vector_double")
    set_proxy_value(double_range_proxy, "vector_double", [1.0, 5.0])

    controller.set_read_only(False)

    # Doesn't accept VectorInt
    assert not controller.visualize_additional_property(int_range_proxy)
    # Accept VectorDouble
    assert controller.visualize_additional_property(double_range_proxy)
    # Allow additional proxy only once.
    assert not controller.visualize_additional_property(double_range_proxy)

    controller.value_update(double_range_proxy)

    # Value in the allowed range
    controller.internal_widget.setText("4.1")

    assert controller.internal_widget.text() == "4.1"
    assert controller.proxy.edit_value == 4.1
    assert "color: black" in controller.internal_widget.styleSheet()

    # Check decimals
    controller.model.decimals = 3
    assert controller.internal_widget.text() == "4.100"

    # Value not in the allowed range
    controller.internal_widget.setText("6.5")

    assert controller.internal_widget.text() == "6.5"
    assert controller.proxy.edit_value is None

    assert "color: red" in controller.internal_widget.styleSheet()


def test_remove_proxy(gui_app: gui_app):
    schema = Object.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="int_prop")

    controller = VectorLimitedIntLineEdit(
        proxy=proxy, model=VectorLimitedIntLineEditModel())
    controller.create(None)
    controller.set_read_only(False)

    set_proxy_value(proxy, "int_prop", 25)

    int_range_proxy = PropertyProxy(root_proxy=root_proxy, path="vector_int")
    set_proxy_value(int_range_proxy, "vector_int", [1, 10])

    assert controller.visualize_additional_property(int_range_proxy)
    assert "color: red" in controller.internal_widget.styleSheet()

    assert controller.remove_additional_property(int_range_proxy)
    assert "color: black" in controller.internal_widget.styleSheet()

    # No longer validation with range_proxy value
    set_proxy_value(proxy, "int_prop", 25)
    assert "color: black" in controller.internal_widget.styleSheet()


def test_int_validator():
    # Without custom min/max
    int_validator = IntValidator()
    validator = LimitedValidator(validator=int_validator, nativeMin=0,
                                 nativeMax=100)

    state, _, _ = validator.validate("50", 0)
    assert state == QValidator.Acceptable

    # With  custom min/max
    validator.setBottom(10)
    validator.setTop(20)
    state, _, _ = validator.validate("50", 0)
    assert not state == QValidator.Acceptable

    # valid value
    state, _, _ = validator.validate("15", 0)
    assert state == QValidator.Acceptable

    # Custom max is higher than native max
    validator.setTop(200)
    state, _, _ = validator.validate("150", 0)
    assert not state == QValidator.Acceptable


def test_double_validator():
    # Without custom min/max
    double_validator = NumberValidator(decimals=2)
    validator = LimitedValidator(validator=double_validator, nativeMin=1.0,
                                 nativeMax=6.0)
    state, _, _ = validator.validate("5.0", 0)
    assert state == QValidator.Acceptable

    # With  custom min/max
    validator.setBottom(2.5)
    validator.setTop(4.5)
    state, _, _ = validator.validate("5.21", 0)
    assert not state == QValidator.Acceptable
    # valid value
    state, _, _ = validator.validate("3.5", 0)
    assert state == QValidator.Acceptable

    # Custom min is smaller than native min
    validator.setBottom(0.0)
    state, _, _ = validator.validate("0.5", 0)
    assert not state == QValidator.Acceptable
