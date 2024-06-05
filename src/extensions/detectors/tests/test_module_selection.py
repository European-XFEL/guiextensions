import pytest

try:
    import cadge  # noqa
except ModuleNotFoundError:
    pytest.skip("`cadge` is not found: skipping the whole tests",
                allow_module_level=True)

from extensions.detectors.module_selection.run_assistant import (
    DETECTOR_GROUPS, RunAssistantModuleSelection)
from karabo.native import (
    AccessMode, Configurable, Hash, String, VectorHash, VectorString)
from karabogui.testing import get_class_property_proxy, set_proxy_value


class ExcludedDevices(Configurable):
    groupId = String(
        displayedName="GroupId",
        defaultValue="",
        accessMode=AccessMode.READONLY)

    sources = VectorString(
        displayedName="Sources",
        defaultValue=[],
        accessMode=AccessMode.READONLY)


class RunAssistant(Configurable):
    excludedDevices = VectorHash(
        displayType="RunAssistant|DeviceSelection",
        defaultValue=[],
        rows=ExcludedDevices,
        displayedName="Excluded devices",)


@pytest.fixture
def controller(gui_app):
    schema = RunAssistant.getClassSchema()
    proxy = get_class_property_proxy(schema, "excludedDevices")
    controller = RunAssistantModuleSelection(proxy=proxy)
    controller.create(None)
    yield controller
    # teardown
    controller.destroy()
    assert controller.widget is None


def test_initial_conditions(controller):
    # Check initial conditions
    assert controller.model.detector == 'SPB: AGIPD1M'
    assert controller.detector_group == DETECTOR_GROUPS['SPB: AGIPD1M']
    assert controller._detector.selection == set(range(16))


def test_valid_load_from_device(controller):
    # First update from the device
    set_proxy_value(controller.proxy,
                    "excludedDevices",
                    [Hash(spb_agipd_sources(range(6)))])
    assert controller._detector.selection == set(range(6, 16))

    # Second update from the device
    set_proxy_value(controller.proxy,
                    "excludedDevices",
                    [Hash(spb_agipd_sources(range(6, 16)))])
    assert controller._detector.selection == set(range(6))


def test_invalid_load_from_device(controller):
    # Update the device with MID AGIPD modules
    set_proxy_value(controller.proxy,
                    "excludedDevices",
                    [Hash(mid_agipd_sources(range(6)))])
    assert controller._detector.selection == set(range(16))


def test_model_instrument_change(controller):
    # First: Update instrument
    controller.model.detector = 'MID: AGIPD1M'
    assert controller.detector_group == DETECTOR_GROUPS['MID: AGIPD1M']

    # Second: update from the device with SPB AGIPD detectors.
    # It shouldn't change the (default) selection
    set_proxy_value(controller.proxy,
                    "excludedDevices",
                    [Hash(spb_agipd_sources(range(6)))])
    assert controller._detector.selection == set(range(16))

    # Third: update from the device with MID AGIPD detectors.
    # It should change the (default) selection
    hsh = Hash(mid_agipd_sources(range(6),
                                 groupId=controller.detector_group.groupId))
    set_proxy_value(controller.proxy, "excludedDevices", [hsh])
    assert controller._detector.selection == set(range(6, 16))


def test_user_input(controller, mocker):
    # Prepare by mocking `send_to_device`
    send_to_device_mock = mocker.patch.object(RunAssistantModuleSelection,
                                              'send_to_device')
    waiting_spy = mocker.spy(RunAssistantModuleSelection, '_waiting')

    # Simulate a user input by setting the detector selection
    controller._detector.selection = set(range(6))
    send_to_device_mock.assert_called_once()
    assert (send_to_device_mock.call_args[0][0]
            == Hash(spb_agipd_sources(range(6, 16))))
    assert controller._is_waiting

    # Now we receive back our changes by simulating a device update
    send_to_device_mock.reset_mock()
    set_proxy_value(controller.proxy,
                    "excludedDevices",
                    [Hash(spb_agipd_sources(range(6, 16)))])
    waiting_spy.assert_called_once()
    assert not controller._is_waiting
    send_to_device_mock.assert_not_called()


# -----------------------------------------------------------------------------
# Helpers


def spb_agipd_sources(modules=range(16), groupId="SPB_AGIPD1M_XTDF"):
    return {
        "groupId": groupId,
        "sources": [f"SPB_DET_AGIPD1M-1/DET/{mod}CH0:xtdf" for mod in modules],
    }


def mid_agipd_sources(modules=range(16), groupId="AGIPD1M_XTDF"):
    return {
        "groupId": groupId,
        "sources": [f"MID_DET_AGIPD1M-1/DET/{mod}CH0:xtdf" for mod in modules],
    }
