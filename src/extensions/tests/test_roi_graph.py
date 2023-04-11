from contextlib import contextmanager
from unittest import mock

import numpy as np

from extensions.roi_graph import RectRoiGraph
from karabo.native import (
    Configurable, EncodingType, Image, ImageData, Node, VectorFloat,
    VectorUInt32)
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


class ObjectNode(Configurable):
    roi1 = VectorUInt32()
    roi2 = VectorFloat()


class BaseRoiGraphTest(GuiTestCase):

    def setUp(self):
        super(BaseRoiGraphTest, self).setUp()
        output_schema = ChannelNode.getClassSchema()
        self.image_proxy = get_class_property_proxy(output_schema, 'data')

        device_schema = ObjectNode.getClassSchema()
        self.roi1_proxy = get_class_property_proxy(device_schema, 'roi1')
        self.roi2_proxy = get_class_property_proxy(device_schema, 'roi2')

        self.controller = RectRoiGraph(proxy=self.image_proxy)
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


@mock.patch('extensions.roi_graph.LabelTableDialog')
class TestRoiLabelChanges(BaseRoiGraphTest):

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
