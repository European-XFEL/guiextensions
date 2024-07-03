from time import sleep

from extensions.display_live_data_indicator import (
    THUMBS_DOWN, THUMBS_UP, LiveDataIndicator)
from extensions.models.api import LiveDataIndicatorModel
from karabo.native import Configurable, Int32, Timestamp
from karabogui.binding.api import DeviceProxy, PropertyProxy, build_binding
from karabogui.conftest import gui_app


class Object(Configurable):
    data = Int32()


def test_icon_update(gui_app: gui_app, mocker):
    """Test the instantiation. Also, the icons when active update and no update
    for the refresh interval time."""
    schema = Object().getDeviceSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(binding=binding, device_id="TestDeviceId")
    proxy = PropertyProxy(root_proxy=root_proxy, path='data')
    controller = LiveDataIndicator(
        proxy=proxy, model=LiveDataIndicatorModel(refresh_interval=1))
    controller.create(parent=None)
    assert controller

    mock_load = mocker.patch.object(controller.widget, 'load', autospec=True)
    proxy.value = 10
    proxy.binding.timestamp = Timestamp()
    controller.value_update(proxy)

    assert mock_load.call_count == 1
    mock_load.assert_called_with(THUMBS_UP)
    mock_load.reset_mock()

    # After 1 seconds of latest value update.
    sleep(1)
    controller.value_update(proxy)
    assert mock_load.call_count == 1
    mock_load.assert_called_with(THUMBS_DOWN)
