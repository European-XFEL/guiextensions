from contextlib import contextmanager

import numpy as np
import pytest

from extensions.zone_plate_graph import ZonePlateGraph
from karabo.native import (
    Configurable, EncodingType, Image, ImageData, Node, VectorUInt32)
from karabogui.testing import get_class_property_proxy, set_proxy_value
from karabogui.util import SignalBlocker


class ImageOutput(Configurable):
    image = Image(data=ImageData(np.zeros((100, 100), dtype=np.uint64),
                                 encoding=EncodingType.GRAY),
                  displayedName="Image")


class Object(Configurable):
    node = Node(ImageOutput)
    roi1 = VectorUInt32(defaultValue=[])
    roi2 = VectorUInt32(defaultValue=[])
    roi3 = VectorUInt32(defaultValue=[])


@contextmanager
def reset_mock(mock_obj):
    mock_obj.reset_mock()
    yield


@pytest.fixture
def controller(gui_app):
    schema = Object.getClassSchema()
    proxy = get_class_property_proxy(schema, 'node')
    controller = ZonePlateGraph(proxy=proxy)
    controller.create(None)
    yield controller
    controller.destroy()
    assert controller.widget is None


@pytest.fixture
def proxies():
    schema = Object.getClassSchema()
    roi1_proxy = get_class_property_proxy(schema, 'roi1')
    roi2_proxy = get_class_property_proxy(schema, 'roi2')
    return roi1_proxy, roi2_proxy


def test_empty(controller):
    assert len(controller.rois) == 0


def test_basics(controller, proxies):
    roi1_proxy, roi2_proxy = proxies
    controller.visualize_additional_property(roi1_proxy)
    controller.visualize_additional_property(roi2_proxy)

    assert len(controller.rois) == 2

    # Check ROIs
    for roi, lines in controller.rois.items():
        # Check traits
        assert roi.geometry == (0, 0, 0, 0)
        assert roi.is_visible is False
        assert roi.label_text == roi.proxy.path
        assert roi.proxy is not None
        # Check Qt item
        assert roi._item_geometry == roi.geometry
        assert roi.roi_item.isVisible() == roi.is_visible
        # Check lines
        for line in lines:
            assert line.value() == 0
            assert line.isVisible() is False


def test_first_device_update(controller, proxies):
    # Mock receiving device update once
    roi1_proxy, roi2_proxy = proxies

    controller.visualize_additional_property(roi1_proxy)
    set_proxy_value(roi1_proxy, 'roi1', (0, 200, 300, 600))

    assert_roi(roi1_proxy, controller, geometry=(0, 200, 300, 600))


def test_second_device_update(controller, proxies):
    roi1_proxy, roi2_proxy = proxies
    # Mock receiving device update twice
    controller.visualize_additional_property(roi1_proxy)
    set_proxy_value(roi1_proxy, 'roi1', (0, 200, 300, 600))
    set_proxy_value(roi1_proxy, 'roi1', (100, 200, 300, 500))

    assert_roi(roi1_proxy, controller, geometry=(100, 200, 300, 500))


def test_user_update(controller, proxies):
    roi1_proxy, roi2_proxy = proxies

    controller.visualize_additional_property(roi1_proxy)

    # Receive one update
    old_geometry = (10, 20, 30, 50)
    set_proxy_value(roi1_proxy, 'roi1', old_geometry)
    assert_roi(roi1_proxy, controller, geometry=old_geometry)

    # Mock changes. Block signal on first change to trigger the ROI
    # movement only once, on the second change.
    roi = controller.get_roi(roi1_proxy)
    item = roi.roi_item
    with SignalBlocker(item):
        item.setPos((100, 300))
    item.setSize((100, 200))
    # Check if ROI has changed with the user changes
    new_geometry = (100, 200, 300, 500)
    assert_roi(roi1_proxy, controller, geometry=new_geometry)
    assert roi.is_waiting

    # Receive an update from the device. Most probably it's still the old
    # value. We ignore the incoming data
    set_proxy_value(roi1_proxy, 'roi1', old_geometry)
    assert_roi(roi1_proxy, controller, geometry=new_geometry)
    assert roi.is_waiting

    # Receive an update from the device. The property has now been updated.
    # value. We confirm that we are ready to receive new data.
    set_proxy_value(roi1_proxy, 'roi1', new_geometry)
    assert_roi(roi1_proxy, controller, geometry=new_geometry)
    assert not roi.is_waiting

    # Receive an update from the device. A newer data has arrived.
    # value. We check if this will apply.
    newer_geometry = old_geometry
    set_proxy_value(roi1_proxy, 'roi1', newer_geometry)
    assert_roi(roi1_proxy, controller, geometry=newer_geometry)
    assert not roi.is_waiting


def test_user_movement(controller, proxies, mocker):
    roi1_proxy, roi2_proxy = proxies
    controller.visualize_additional_property(roi1_proxy)

    # Receive one update
    old_geometry = (10, 20, 30, 50)
    mocked_send_changes = mocker.patch(
        "extensions.roi_graph.send_property_changes")
    with reset_mock(mocked_send_changes):
        set_proxy_value(roi1_proxy, 'roi1', old_geometry)
    assert_roi(roi1_proxy, controller, geometry=old_geometry)
    mocked_send_changes.assert_not_called()

    # Start user movement.
    roi = controller.get_roi(roi1_proxy)
    item = roi.roi_item
    with reset_mock(mocked_send_changes):
        item._moveStarted()
        with SignalBlocker(item):
            item.setPos((100, 300))
            item.setSize((100, 200))
        item.sigRegionChanged.emit(item)
    new_geometry = (100, 200, 300, 500)
    # Check if ROI has changed with the user changes
    assert_roi(roi1_proxy, controller, geometry=new_geometry)
    mocked_send_changes.assert_not_called()

    # Check if device changes are ignored when the ROI is moving
    newer_geometry = old_geometry
    with reset_mock(mocked_send_changes):
        set_proxy_value(roi1_proxy, 'roi1', newer_geometry)
    assert_roi(roi1_proxy, controller, geometry=new_geometry)
    mocked_send_changes.assert_not_called()

    # Finish user movement
    with reset_mock(mocked_send_changes):
        with SignalBlocker(item):
            item.setPos((10, 30))
            item.setSize((10, 20))
        item.sigRegionChanged.emit(item)
        item._moveFinished()
    # Check if ROI has changed with the user changes
    assert_roi(roi1_proxy, controller, geometry=newer_geometry)
    mocked_send_changes.assert_called_once()


def assert_roi(proxy, controller, *, geometry):
    roi = controller.get_roi(proxy)
    # Check traits
    assert roi.geometry == tuple(geometry)
    assert roi.is_visible is True
    # Check Qt item
    assert roi._item_geometry == roi.geometry
    assert roi.roi_item.isVisible() is roi.is_visible
    # Check lines
    for line, value in zip(controller.rois[roi], geometry):
        assert line.value() == value
