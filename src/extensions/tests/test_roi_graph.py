from contextlib import contextmanager
from unittest import mock

import numpy as np
import pytest

from extensions.roi_graph import CircleRoiGraph, RectRoiGraph, TableRoiGraph
from karabo.native import (
    Configurable, EncodingType, Hash, Image, ImageData, Node, String, UInt32,
    VectorFloat, VectorHash, VectorInt32, VectorUInt32)
from karabogui.binding.api import (
    DeviceProxy, PropertyProxy, ProxyStatus, build_binding)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)
from karabogui.util import SignalBlocker


# Output channel
class DataNode(Configurable):
    image = Image(data=ImageData(np.zeros((500, 500), dtype=np.float64),
                                 encoding=EncodingType.GRAY),
                  displayedName="Image")


class ChannelNode(Configurable):
    data = Node(DataNode)


class RoiTableSchema(Configurable):
    label = String()
    roi = VectorInt32()


class Device(Configurable):
    # General settings
    output = Node(ChannelNode)

    # For RectRoiGraph
    roi1 = VectorUInt32()
    roi2 = VectorFloat()

    # For CircleRoiGraph
    center = VectorUInt32()
    radius = UInt32()

    # For TableRoiGraph
    roiTable = VectorHash(
        rows=RoiTableSchema,
        displayType='TableRoiValues')


class AdditionalNode(Configurable):
    center = VectorUInt32()
    radius = UInt32()


class BaseRoiGraphTest(GuiTestCase):

    controller_klass = None

    def setUp(self):
        super(BaseRoiGraphTest, self).setUp()
        output_schema = ChannelNode.getClassSchema()
        self.image_proxy = get_class_property_proxy(output_schema,
                                                    'data.image')

        device_schema = Device.getClassSchema()
        self.roi1_proxy = get_class_property_proxy(device_schema, 'roi1')
        self.roi2_proxy = get_class_property_proxy(device_schema, 'roi2')
        self.center_proxy = get_class_property_proxy(device_schema, 'center')
        self.radius_proxy = get_class_property_proxy(device_schema, 'radius')

        self.controller = self.controller_klass(proxy=self.image_proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    @property
    def model(self):
        return self.controller.model

    @contextmanager
    def reset_mock(self, mock_obj):
        mock_obj.reset_mock()
        yield


@mock.patch('extensions.roi_graph.send_property_changes')
class TestRectRoiGraph(BaseRoiGraphTest):

    controller_klass = RectRoiGraph

    def test_basics(self, *mocks):
        # Check ROIs
        assert len(self.controller.rois) == 0

    def test_one_roi_update(self, *mocks):
        self.controller.visualize_additional_property(self.roi1_proxy)

        # Mock receivng device update once
        set_proxy_value(self.roi1_proxy, 'roi1', [0, 200, 300, 600])
        self._assert_roi(roi=self.controller.get_roi(self.roi1_proxy),
                         geometry=[0, 200, 300, 600])

    def test_two_roi_update(self, *mocks):
        self.controller.visualize_additional_property(self.roi1_proxy)
        self.controller.visualize_additional_property(self.roi2_proxy)

        # Mock receivng device update once
        set_proxy_value(self.roi1_proxy, 'roi1', [0, 200, 300, 600])
        self._assert_roi(roi=self.controller.get_roi(self.roi1_proxy),
                         geometry=[0, 200, 300, 600])
        set_proxy_value(self.roi2_proxy, 'roi2', [100, 500, 400, 700])
        self._assert_roi(roi=self.controller.get_roi(self.roi2_proxy),
                         geometry=[100, 500, 400, 700])

    def test_user_update(self, *mocks):
        # Prepare one ROI property
        self.controller.visualize_additional_property(self.roi1_proxy)
        old_geometry = (10, 20, 30, 50)
        set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        roi = self.controller.get_roi(self.roi1_proxy)

        # Receive one update
        set_proxy_value(self.roi1_proxy, 'roi1', [0, 200, 300, 600])

        # Mock changes. Block signal on first change to trigger the ROI
        # movement only once, on the second change.
        item = roi.roi_item
        with SignalBlocker(item):
            item.setPos((100, 300))
        item.setSize((100, 200))
        # Check if ROI has changed with the user changes
        new_geometry = (100, 200, 300, 500)
        self._assert_roi(roi, new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. Most probably it's still the old
        # value. We ignore the incoming data
        set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        self._assert_roi(roi, new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. The property has now been updated.
        # value. We confirm that we are ready to receive new data.
        set_proxy_value(self.roi1_proxy, 'roi1', new_geometry)
        self._assert_roi(roi, new_geometry)
        assert roi.is_waiting is False

        # Receive an update from the device. A newer data has arrived.
        # value. We check if this will apply.
        newer_geometry = old_geometry
        set_proxy_value(self.roi1_proxy, 'roi1', newer_geometry)
        self._assert_roi(roi, newer_geometry)
        assert roi.is_waiting is False

    def test_user_movement(self, mocked_send_changes):
        # Prepare one ROI property
        self.controller.visualize_additional_property(self.roi1_proxy)
        old_geometry = (10, 20, 30, 50)
        set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        roi = self.controller.get_roi(self.roi1_proxy)

        # Receive one update
        with self.reset_mock(mocked_send_changes):
            set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        mocked_send_changes.assert_not_called()

        # Start user movement.
        item = roi.roi_item
        with self.reset_mock(mocked_send_changes):
            item._moveStarted()
            with SignalBlocker(item):
                item.setPos((100, 300))
                item.setSize((100, 200))
            item.sigRegionChanged.emit(item)
        new_geometry = (100, 200, 300, 500)
        # Check if ROI has changed with the user changes
        self._assert_roi(roi, new_geometry)
        mocked_send_changes.assert_not_called()

        # Check if device changes are ignored when the ROI is moving
        newer_geometry = old_geometry
        with self.reset_mock(mocked_send_changes):
            set_proxy_value(self.roi1_proxy, 'roi1', newer_geometry)
        self._assert_roi(roi, new_geometry)
        mocked_send_changes.assert_not_called()

        # Finish user movement
        with self.reset_mock(mocked_send_changes):
            with SignalBlocker(item):
                item.setPos((10, 30))
                item.setSize((10, 20))
            item.sigRegionChanged.emit(item)
            item._moveFinished()
        # Check if ROI has changed with the user changes
        self._assert_roi(roi, newer_geometry)
        mocked_send_changes.assert_called_once()

    # ---------------------------------------------------------------------
    # Helpers

    def _assert_roi(self, roi, geometry):
        assert roi.geometry == tuple(geometry)
        assert roi.is_visible is True
        # Check Qt item
        assert roi._item_geometry == roi.geometry
        assert roi.roi_item.isVisible() is roi.is_visible


@mock.patch('extensions.roi_graph.send_property_changes')
class TestCircleRoiGraph(BaseRoiGraphTest):

    controller_klass = CircleRoiGraph

    def test_empty(self, *mocks):
        # Check ROIs
        assert len(self.controller.rois) == 0

    def test_incomplete_roi_only_radius(self, *mocks):
        self.controller.visualize_additional_property(self.radius_proxy)
        assert len(self.controller.rois) == 1
        self._assert_roi(roi=self.controller.roi, visible=False)

        # Mock receiving device update once
        set_proxy_value(self.radius_proxy, 'radius', 10)
        self._assert_roi(roi=self.controller.roi, radius=10, visible=False)

    def test_incomplete_roi_second_radius(self, *mocks):
        # Check the proxies of the created ROI after adding two proxies
        self.controller.visualize_additional_property(self.radius_proxy)
        assert len(self.controller.rois) == 1
        assert not self.controller.roi.is_complete
        assert self.controller.roi.radius_proxy is self.radius_proxy

        # Add a second radius: we expect for it to be ignored
        second_radius = self._get_additional_proxy('radius')
        self.controller.visualize_additional_property(second_radius)
        assert len(self.controller.rois) == 1
        assert not self.controller.roi.is_complete
        assert self.controller.roi.radius_proxy is self.radius_proxy

    def test_incomplete_roi_only_center(self, *mocks):
        self.controller.visualize_additional_property(self.center_proxy)
        assert len(self.controller.rois) == 1
        self._assert_roi(roi=self.controller.roi, visible=False)

        # Mock receiving device update once
        set_proxy_value(self.center_proxy, 'center', (200, 300))
        self._assert_roi(roi=self.controller.roi,
                         center=(200, 300), visible=False)

    def test_incomplete_roi_second_center(self, *mocks):
        # Check the proxies of the created ROI after adding two proxies
        self.controller.visualize_additional_property(self.center_proxy)
        assert len(self.controller.rois) == 1
        assert not self.controller.roi.is_complete
        assert self.controller.roi.center_proxy is self.center_proxy

        # Add a second center: we expect for it to be ignored
        second_center = self._get_additional_proxy('center')
        self.controller.visualize_additional_property(second_center)
        assert len(self.controller.rois) == 1
        assert not self.controller.roi.is_complete
        assert self.controller.roi.center_proxy is self.center_proxy

    def test_complete_roi(self, *mocks):
        self.controller.visualize_additional_property(self.center_proxy)
        self.controller.visualize_additional_property(self.radius_proxy)
        assert len(self.controller.rois) == 1
        self._assert_roi(roi=self.controller.roi, visible=False)

        set_proxy_value(self.radius_proxy, 'radius', 10)
        self._assert_roi(roi=self.controller.roi, radius=10)
        set_proxy_value(self.center_proxy, 'center', (200, 300))
        self._assert_roi(roi=self.controller.roi, radius=10, center=(200, 300))

    def test_complete_roi_second_proxy(self, *mocks):
        # Check the proxies of the created ROI after adding two proxies
        self.controller.visualize_additional_property(self.radius_proxy)
        self.controller.visualize_additional_property(self.center_proxy)
        assert len(self.controller.rois) == 1
        assert self.controller.roi.is_complete
        assert self.controller.roi.center_proxy is self.center_proxy
        assert self.controller.roi.radius_proxy is self.radius_proxy

        # Add a second center: we expect for it to be ignored
        second_center = self._get_additional_proxy('center')
        self.controller.visualize_additional_property(second_center)
        assert len(self.controller.rois) == 1
        assert self.controller.roi.is_complete
        assert self.controller.roi.center_proxy is self.center_proxy
        assert self.controller.roi.radius_proxy is self.radius_proxy

        # Add a second radius: we expect for it to be ignored
        second_radius = self._get_additional_proxy('radius')
        self.controller.visualize_additional_property(second_radius)
        assert len(self.controller.rois) == 1
        assert self.controller.roi.is_complete
        assert self.controller.roi.center_proxy is self.center_proxy
        assert self.controller.roi.radius_proxy is self.radius_proxy

    def _assert_roi(self, roi, radius=0, center=(0, 0), visible=True):
        assert roi.radius == radius
        assert roi.center == tuple(center)
        assert roi.is_visible is visible
        # Check Qt item
        assert roi._item_radius == roi.radius
        assert roi._item_center == roi.center
        assert roi.roi_item.isVisible() is roi.is_visible

    @staticmethod
    def _get_additional_proxy(prop):
        return get_class_property_proxy(AdditionalNode.getClassSchema(), prop)


@mock.patch('extensions.roi_graph.LabelTableDialog')
class TestRoiLabelChanges(BaseRoiGraphTest):

    controller_klass = RectRoiGraph

    def setUp(self):
        super().setUp()
        for proxy in [self.roi1_proxy, self.roi2_proxy]:
            self.controller.visualize_additional_property(proxy)

    def test_basics(self, mocked_dialog):
        self.assertListEqual(self.model.labels, ['', ''])

    def test_first_call(self, mocked_dialog):
        # Return intermittently
        mocked_dialog.get.return_value = (None, False)

        self.controller._edit_labels()
        mocked_dialog.get.assert_called_with(
            {"names": ['roi1', 'roi2'],
             "labels": ['', ''], },
            parent=self.controller.widget
        )

    def test_first_update(self, mocked_dialog):
        # Return with proper value
        config = {"names": ['roi1', 'roi2'],
                  "labels": ['foo', 'bar'], }
        mocked_dialog.get.return_value = (config, True)

        self.controller._edit_labels()
        self.assertListEqual(self.model.labels, config["labels"])
        zipped = zip((self.roi1_proxy, self.roi2_proxy), config["labels"])
        for proxy, label in zipped:
            roi = self.controller.get_roi(proxy)
            self.assertEqual(roi.label_text, label)

    def test_second_call(self, mocked_dialog):
        # First call: return with initial value
        config = {"names": ['roi1', 'roi2'],
                  "labels": ['foo', 'bar'], }
        mocked_dialog.get.return_value = (config, True)
        self.controller._edit_labels()

        # Second call: return intermittently
        mocked_dialog.reset_mock()
        mocked_dialog.get.return_value = (None, False)
        self.controller._edit_labels()
        mocked_dialog.get.assert_called_with(
            {"names": ['roi1', 'roi2'],
             "labels": ['foo', 'bar']},
            parent=self.controller.widget)


# I'll try to convert the rest of this test into `pytest` soon(tm).
# I would start now with the Table ROI Graph.

# -----------------------------------------------------------------------------
# TableRoiGraph


@pytest.fixture
def device_proxy(gui_app):
    schema = Device.getClassSchema()
    binding = build_binding(schema)
    device = DeviceProxy(device_id="Device",
                         server_id="Server",
                         binding=binding,
                         status=ProxyStatus.OFFLINE)
    return device


@pytest.fixture(name='trg_controller')
def table_roi_graph_controller(device_proxy):
    proxy = PropertyProxy(root_proxy=device_proxy, path="output.data.image")
    controller = TableRoiGraph(proxy=proxy)
    controller.create(None)
    yield controller
    controller.destroy()
    assert controller.widget is None


@pytest.fixture
def roi_table_proxy(device_proxy):
    return PropertyProxy(root_proxy=device_proxy, path="roiTable")


@pytest.fixture
def roi_table_proxy_with_default_value(roi_table_proxy):
    roi1 = {'label': 'ROI 1', 'roi': [100, 200, 100, 200]}
    roi2 = {'label': 'ROI 2', 'roi': [300, 400, 300, 400]}
    set_proxy_value(roi_table_proxy, 'roiTable', [Hash(roi1), Hash(roi2)])
    return roi_table_proxy, [roi1, roi2]


def test_table_roi_graph_basics(trg_controller):
    assert trg_controller._roi_proxy is None
    assert len(trg_controller.rois) == 0


def test_table_roi_graph_with_empty_table(trg_controller, roi_table_proxy):
    trg_controller.visualize_additional_property(roi_table_proxy)

    assert trg_controller._roi_proxy is roi_table_proxy
    assert len(trg_controller.rois) == 0


def test_table_roi_graph_with_valid_table(trg_controller,
                                          roi_table_proxy_with_default_value):
    proxy, default_value = roi_table_proxy_with_default_value
    trg_controller.visualize_additional_property(proxy)

    assert len(trg_controller.rois) == 2
    for expected_val, actual_obj in zip(default_value, trg_controller.rois):
        assert expected_val['label'] == actual_obj.label_text
        assert tuple(expected_val['roi']) == actual_obj.geometry


def test_table_roi_graph_with_moved_roi(trg_controller,
                                        roi_table_proxy_with_default_value,
                                        mocker):
    call_device_slot = 'extensions.roi_graph.call_device_slot'
    mock_call_device_slot = mocker.patch(call_device_slot)

    proxy, default_value = roi_table_proxy_with_default_value
    trg_controller.visualize_additional_property(proxy)
    roi = trg_controller.rois[0]

    # Start user movement.
    item = roi.roi_item
    item._moveStarted()
    with SignalBlocker(item):
        item.setPos((100, 300))
        item.setSize((100, 200))
    item.sigRegionChanged.emit(item)
    item._moveFinished()
    new_geometry = (100, 200, 300, 500)

    assert roi.geometry == new_geometry
    assert trg_controller.is_waiting is True

    mock_call_device_slot.assert_called()
    actual = mock_call_device_slot.call_args[1].get('table')
    expected = [Hash(value) for value in default_value]
    expected[0]['roi'] = list(new_geometry)
    assert actual == expected
