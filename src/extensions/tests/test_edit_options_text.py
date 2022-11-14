from qtpy.QtGui import QValidator

from karabo.common.states import State
from karabo.native import Configurable, Hash, String, VectorString
from karabogui.api import PropertyProxy, build_binding
from karabogui.binding.api import DeviceProxy
from karabogui.conftest import gui_app
from karabogui.testing import set_proxy_hash, set_proxy_value

from ..edit_text_options import EditableTextOptions, OptionValidator
from ..models.api import EditableTextOptionsModel


class Object(Configurable):
    state = String(
        defaultValue=State.INIT)
    prop = String(
        defaultValue="wuff",
        allowedStates=[State.INIT])
    textOptions = VectorString(
        defaultValue=["wuff", "blob", "hello"],
        allowedStates=[State.INIT])


def test_editable_options(gui_app: gui_app):
    binding = build_binding(Object.getClassSchema())
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")

    proxy = PropertyProxy(root_proxy=root_proxy, path="prop")
    controller = EditableTextOptions(
        proxy=proxy,
        model=EditableTextOptionsModel(strict=True))
    controller.create(None)
    controller.set_read_only(False)

    # 1. set the value
    h = Hash("prop", "wuff")
    set_proxy_hash(proxy, h)
    assert controller.internal_widget.text() == "wuff"

    def stylesheet(color):
        nonlocal controller
        return color in controller.internal_widget.styleSheet()

    assert stylesheet("black")
    h = Hash("prop", "blob")
    set_proxy_hash(proxy, h)
    assert controller.internal_widget.text() == "blob"
    assert stylesheet("black")

    # 2. state update
    set_proxy_value(proxy, "state", "CHANGING")
    assert not controller.internal_widget.isEnabled()
    set_proxy_value(proxy, "state", "INIT")
    assert controller.internal_widget.isEnabled()
    set_proxy_value(proxy, "state", "CHANGING")
    assert not controller.internal_widget.isEnabled()

    # 3. Add options proxy
    options_proxy = PropertyProxy(root_proxy=root_proxy, path="textOptions")
    assert options_proxy.binding is not None
    assert controller.visualize_additional_property(options_proxy)
    # Try add a second time, but options proxy is already set
    assert not controller.visualize_additional_property(options_proxy)
    set_proxy_value(options_proxy, "textOptions", ["wuff", "blob", "hello"])

    # 4. External value update, conflict
    h = Hash("prop", "notinoptions")
    set_proxy_hash(proxy, h)
    assert controller.internal_widget.text() == "notinoptions"
    assert stylesheet("red")

    # 5. Resolve conflict
    h = Hash("prop", "blob")
    set_proxy_hash(proxy, h)
    assert controller.internal_widget.text() == "blob"
    assert stylesheet("black")

    # 6. Edit value, conflict on the way
    controller.internal_widget.setText("wuf")
    assert controller.internal_widget.text() == "wuf"
    assert stylesheet("red")
    assert proxy.edit_value is None

    # 7. Edit value, valid
    controller.internal_widget.setText("wuff")
    assert controller.internal_widget.text() == "wuff"
    assert stylesheet("black")
    assert proxy.edit_value == "wuff"
    set_proxy_value(proxy, "prop", "wuff")

    # 8. Options change, conflict and resolve
    set_proxy_value(options_proxy, "textOptions", ["notontheproxy"])
    assert controller.internal_widget.text() == "wuff"
    assert stylesheet("red")
    set_proxy_value(options_proxy, "textOptions", ["wuff"])
    assert stylesheet("black")

    # Remove additional proxy
    assert controller.remove_additional_property(options_proxy)
    assert controller.option_proxy is None
    assert not controller.remove_additional_property(options_proxy)
    assert controller.validator._options == []

    # Changing  model value should update the validator.
    controller.model.strict = True
    assert controller.validator._strict
    controller.model.strict = False
    assert not controller.validator._strict


def test_options_validator(gui_app):
    validator = OptionValidator(strict=True)
    validator.setOptions([])
    # Empty options all accepted, similar to allowed states
    result, _, _ = validator.validate("", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("Notcat", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("dog#11", None)
    assert result == QValidator.Acceptable

    # provide options
    validator.setOptions(["dog", "cat", "eagle"])
    result, _, _ = validator.validate("", None)
    assert result == QValidator.Intermediate
    result, _, _ = validator.validate("dog", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("d", None)
    assert result == QValidator.Intermediate
    result, _, _ = validator.validate("dog", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("dogg", None)
    assert result == QValidator.Invalid
    result, _, _ = validator.validate("agl", None)
    assert result == QValidator.Invalid

    # Other options
    result, _, _ = validator.validate("cat", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("eagle", None)
    assert result == QValidator.Acceptable

    # Set validator non strict
    validator = OptionValidator(strict=False)
    validator.setOptions(["dog", "cat", "eagle"])
    result, _, _ = validator.validate("", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("nodog", None)
    assert result == QValidator.Acceptable
    result, _, _ = validator.validate("###", None)
    assert result == QValidator.Acceptable
