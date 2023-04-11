from contextlib import contextmanager
from unittest import mock

import numpy as np

from extensions.zone_plate_graph import ZonePlateGraph
from karabo.native import (
    Configurable, EncodingType, Image, ImageData, Node, VectorUInt32)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)
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


@mock.patch('extensions.roi_graph.send_property_changes')
class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = ZonePlateGraph(proxy=self.proxy)
        self.controller.create(None)

        self.roi1_proxy = get_class_property_proxy(schema, 'roi1')
        self.roi2_proxy = get_class_property_proxy(schema, 'roi2')
        self.roi3_proxy = get_class_property_proxy(schema, 'roi3')

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_empty(self, *_):
        assert len(self.controller.rois) == 0

    def test_basics(self, *_):
        self.controller.visualize_additional_property(self.roi1_proxy)
        self.controller.visualize_additional_property(self.roi2_proxy)

        assert len(self.controller.rois) == 2

        # Check ROIs
        for roi, lines in self.controller.rois.items():
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

    def test_first_device_update(self, *_):
        # Mock receivng device update once
        self.controller.visualize_additional_property(self.roi1_proxy)
        set_proxy_value(self.roi1_proxy, 'roi1', (0, 200, 300, 600))

        self.assert_roi(self.roi1_proxy, geometry=(0, 200, 300, 600))

    def test_second_device_update(self, *_):
        # Mock receivng device update twice
        self.controller.visualize_additional_property(self.roi1_proxy)
        set_proxy_value(self.roi1_proxy, 'roi1', (0, 200, 300, 600))
        set_proxy_value(self.roi1_proxy, 'roi1', (100, 200, 300, 500))

        self.assert_roi(self.roi1_proxy, geometry=(100, 200, 300, 500))

    def test_user_update(self, *_):
        self.controller.visualize_additional_property(self.roi1_proxy)

        # Receive one update
        old_geometry = (10, 20, 30, 50)
        set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        self.assert_roi(self.roi1_proxy, geometry=old_geometry)

        # Mock changes. Block signal on first change to trigger the ROI
        # movement only once, on the second change.
        roi = self.controller.get_roi(self.roi1_proxy)
        item = roi.roi_item
        with SignalBlocker(item):
            item.setPos((100, 300))
        item.setSize((100, 200))
        # Check if ROI has changed with the user changes
        new_geometry = (100, 200, 300, 500)
        self.assert_roi(self.roi1_proxy, geometry=new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. Most probably it's still the old
        # value. We ignore the incoming data
        set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        self.assert_roi(self.roi1_proxy, geometry=new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. The property has now been updated.
        # value. We confirm that we are ready to receive new data.
        set_proxy_value(self.roi1_proxy, 'roi1', new_geometry)
        self.assert_roi(self.roi1_proxy, geometry=new_geometry)
        assert roi.is_waiting is False

        # Receive an update from the device. A newer data has arrived.
        # value. We check if this will apply.
        newer_geometry = old_geometry
        set_proxy_value(self.roi1_proxy, 'roi1', newer_geometry)
        self.assert_roi(self.roi1_proxy, geometry=newer_geometry)
        assert roi.is_waiting is False

    def test_user_movement(self, mocked_send_changes):
        self.controller.visualize_additional_property(self.roi1_proxy)

        # Receive one update
        old_geometry = (10, 20, 30, 50)
        with self.reset_mock(mocked_send_changes):
            set_proxy_value(self.roi1_proxy, 'roi1', old_geometry)
        self.assert_roi(self.roi1_proxy, geometry=old_geometry)
        mocked_send_changes.assert_not_called()

        # Start user movement.
        roi = self.controller.get_roi(self.roi1_proxy)
        item = roi.roi_item
        with self.reset_mock(mocked_send_changes):
            item._moveStarted()
            with SignalBlocker(item):
                item.setPos((100, 300))
                item.setSize((100, 200))
            item.sigRegionChanged.emit(item)
        new_geometry = (100, 200, 300, 500)
        # Check if ROI has changed with the user changes
        self.assert_roi(self.roi1_proxy, geometry=new_geometry)
        mocked_send_changes.assert_not_called()

        # Check if device changes are ignored when the ROI is moving
        newer_geometry = old_geometry
        with self.reset_mock(mocked_send_changes):
            set_proxy_value(self.roi1_proxy, 'roi1', newer_geometry)
        self.assert_roi(self.roi1_proxy, geometry=new_geometry)
        mocked_send_changes.assert_not_called()

        # Finish user movement
        with self.reset_mock(mocked_send_changes):
            with SignalBlocker(item):
                item.setPos((10, 30))
                item.setSize((10, 20))
            item.sigRegionChanged.emit(item)
            item._moveFinished()
        # Check if ROI has changed with the user changes
        self.assert_roi(self.roi1_proxy, geometry=newer_geometry)
        mocked_send_changes.assert_called_once()

    # ---------------------------------------------------------------------
    # Helpers

    def assert_roi(self, proxy, *, geometry):
        roi = self.controller.get_roi(proxy)
        # Check traits
        assert roi.geometry == tuple(geometry)
        assert roi.is_visible is True
        # Check Qt item
        assert roi._item_geometry == roi.geometry
        assert roi.roi_item.isVisible() is roi.is_visible
        # Check lines
        for line, value in zip(self.controller.rois[roi], geometry):
            assert line.value() == value

    @property
    def widget(self):
        return self.controller.widget

    @contextmanager
    def reset_mock(self, mock_obj):
        mock_obj.reset_mock()
        yield
