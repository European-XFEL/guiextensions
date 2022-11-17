from qtpy.QtGui import QValidator

from extensions.edit_limited_lineedit import (
    LimitedDoubleLineEdit, LimitedIntLineEdit, LimitedValidator,
    VectorLimitedDoubleLineEdit, VectorLimitedIntLineEdit)
from extensions.models.api import (
    LimitedDoubleLineEditModel, LimitedIntLineEditModel,
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
    min_int = Int32(minInc=-10, maxInc=10, allowedStates=[State.INIT],
                    defaultValue=0)
    max_int = Int32(minInc=-10, maxInc=10, allowedStates=[State.INIT],
                    defaultValue=10)

    min_double = Double(allowedStates=[State.INIT], defaultValue=1.0)
    max_double = Double(allowedStates=[State.INIT], defaultValue=3.0)


def test_vector_limited_int_line_edit(gui_app: gui_app):
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

    # Before any additional proxy set the Int32 max value.
    controller.internal_widget.setText("2147483648")
    assert "color: red" in controller.internal_widget.styleSheet()
    assert controller.internal_widget.text() == "2147483648"

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


def test_vector_limited_double_line_edit(gui_app: gui_app):
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

    controller.internal_widget.setText("5.0")
    assert "color: black" in controller.internal_widget.styleSheet()
    controller.model.decimals = 4
    assert "color: black" in controller.internal_widget.styleSheet()


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

    # Still validate the Int32 native min
    controller.internal_widget.setText("-2147483649")
    assert "color: red" in controller.internal_widget.styleSheet()
    assert controller.internal_widget.text() == "-2147483649"


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


def test_int_line_edit(gui_app: gui_app):
    schema = Object.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="int_prop")

    controller = LimitedIntLineEdit(
        proxy=proxy, model=LimitedIntLineEditModel())
    controller.create(None)
    controller.set_read_only(False)
    set_proxy_value(proxy, "int_prop", 25)

    # Without adding any additional proxies.
    assert "color: black" in controller.internal_widget.styleSheet()
    assert controller.internal_widget.text() == "25"
    assert controller.proxy.edit_value is None

    # Add one additional proxy
    min_int_proxy = PropertyProxy(root_proxy=root_proxy, path="min_int")
    set_proxy_value(min_int_proxy, "min_int", 1)
    assert min_int_proxy.binding
    assert controller.visualize_additional_property(min_int_proxy)
    assert "color: black" in controller.internal_widget.styleSheet()

    # Add one more proxy and make the current value out of range.
    max_int_proxy = PropertyProxy(root_proxy=root_proxy, path="max_int")
    assert max_int_proxy.binding
    set_proxy_value(max_int_proxy, "max_int", 15)

    assert controller.visualize_additional_property(max_int_proxy)
    assert "color: red" in controller.internal_widget.styleSheet()
    assert controller.proxy.edit_value is None
    assert controller.internal_widget.text() == "25"

    # Set the value to be in allowed range.
    controller.internal_widget.setText("10")
    assert "color: black" in controller.internal_widget.styleSheet()
    assert controller.proxy.edit_value == 10

    # Update max_int proxy value to make the value invalid.
    set_proxy_value(max_int_proxy, "max_int", 5)
    assert "color: red" in controller.internal_widget.styleSheet()
    assert controller.internal_widget.text() == "10"

    # Remove Proxy.
    controller.remove_additional_property(min_int_proxy)
    assert "color: black" in controller.internal_widget.styleSheet()
    # No more validation after removing one of the additional proxies.
    controller.internal_widget.setText("100")
    assert controller.internal_widget.text() == "100"
    assert controller.proxy.edit_value == 100


def test_double_line_edit(gui_app: gui_app):
    schema = Object.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="double_prop")
    controller = LimitedDoubleLineEdit(
        proxy=proxy, model=LimitedDoubleLineEditModel())
    controller.create(None)
    controller.set_read_only(False)

    # Add one additional proxy
    max_double_proxy = PropertyProxy(root_proxy=root_proxy, path="max_double")
    set_proxy_value(max_double_proxy, "max_double", 3.0)
    assert max_double_proxy.binding
    assert controller.visualize_additional_property(max_double_proxy)

    # Add one more proxy.
    min_double_proxy = PropertyProxy(root_proxy=root_proxy, path="min_double")
    set_proxy_value(min_double_proxy, "min_double", 1.0)
    assert min_double_proxy.binding
    assert controller.visualize_additional_property(min_double_proxy)

    assert "color: red" in controller.internal_widget.styleSheet()

    # Update the value to be in the range.
    controller.internal_widget.setText("2.5")
    assert "color: black" in controller.internal_widget.styleSheet()
    assert controller.proxy.edit_value == 2.5
    assert controller.internal_widget.text() == "2.5"

    # Update additional proxy value to make the current value invalid, again.
    set_proxy_value(min_double_proxy, "min_double", 2.9)
    assert controller.internal_widget.text() == "2.5"
    assert "color: red" in controller.internal_widget.styleSheet()


def test_decimals(gui_app, mocker):
    schema = Object.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="double_prop")
    controller = LimitedDoubleLineEdit(
        proxy=proxy, model=LimitedDoubleLineEditModel())
    controller.create(None)
    controller.set_read_only(False)
    set_proxy_value(proxy, "double_prop", 9.123456789)
    internal_widget = controller.internal_widget
    assert internal_widget.text() == "9.123456789"

    # Action menu-item
    action = controller.widget.actions()[0]
    assert action.text() == "Change number of decimals"
    dialog_path = "extensions.edit_limited_lineedit.QInputDialog"
    input_dialog = mocker.patch(dialog_path)
    input_dialog.getInt.return_value = 5, True
    action.trigger()

    assert controller.model.decimals == 5

    # test _decimal_update
    assert internal_widget.text() == "9.12346"

    controller.model.decimals = 3
    assert internal_widget.text() == "9.123"

    controller.model.decimals = 1
    assert internal_widget.text() == "9.1"

    controller.model.decimals = 8
    assert internal_widget.text() == "9.12345679"
