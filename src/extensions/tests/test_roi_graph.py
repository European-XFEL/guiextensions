from contextlib import contextmanager
from unittest import mock

import numpy as np

from extensions.display_roi_graph import RectRoiGraph
from karabo.native import (
    Configurable, EncodingType, Hash, Image, ImageData, Node, VectorUInt32)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)
from karabogui.util import SignalBlocker


class ImageOutput(Configurable):
    image = Image(data=ImageData(np.zeros((100, 100), dtype=np.uint64),
                                 encoding=EncodingType.GRAY),
                  displayedName="Image")


class OutputNode(Configurable):
    roi = VectorUInt32(defaultValue=[])
    outputImage = Node(ImageOutput)


class Object(Configurable):
    node = Node(OutputNode)


@mock.patch('extensions.display_roi_graph.send_property_changes')
@mock.patch.object(RectRoiGraph, '_set_image')
class TestRectRoiGraph(GuiTestCase):
    def setUp(self):
        super(TestRectRoiGraph, self).setUp()
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = RectRoiGraph(proxy=self.proxy)
        self.controller.create(None)

        self._values_cache = {
            'roi': [10, 20, 10, 20],
        }

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_basics(self, *mocks):
        # Check ROIs
        for name, roi in self.rois.items():
            # Check traits
            assert roi.geometry == (0, 0, 0, 0)
            assert roi.is_visible is False
            assert roi.path == name
            assert roi.proxy is not None
            # Check Qt item
            assert roi._item_geometry == roi.geometry
            assert roi.roi_item.isVisible() == roi.is_visible

    def test_first_device_update(self, *mocks):
        # Mock receivng device update once
        self.update_proxy()
        self.assert_roi()

    def test_second_device_update(self, *mocks):
        # Mock receivng device update twice
        self.update_proxy()
        self.update_proxy(roi=(100, 200, 300, 500))
        self.assert_roi(roi=(100, 200, 300, 500))

    def test_user_update(self, *mocks):
        # Receive one update
        old_geometry = (10, 20, 30, 50)
        self.update_proxy(roi=old_geometry)
        self.assert_roi(roi=old_geometry)

        # Mock changes. Block signal on first change to trigger the ROI
        # movement only once, on the second change.
        roi = self.rois['roi']
        item = roi.roi_item
        with SignalBlocker(item):
            item.setPos((100, 300))
        item.setSize((100, 200))
        # Check if ROI has changed with the user changes
        new_geometry = (100, 200, 300, 500)
        self.assert_roi(roi=new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. Most probably it's still the old
        # value. We ignore the incoming data
        self.update_proxy(roi=old_geometry)
        self.assert_roi(roi=new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. The property has now ben updated.
        # value. We confirm that we are ready to receive new data.
        self.update_proxy(roi=new_geometry)
        self.assert_roi(roi=new_geometry)
        assert roi.is_waiting is False

        # Receive an update from the device. A newer data has arrived.
        # value. We check if this will apply.
        newer_geometry = old_geometry
        self.update_proxy(roi=newer_geometry)
        self.assert_roi(roi=newer_geometry)
        assert roi.is_waiting is False

    def test_user_movement(self, _, mocked_send_changes):
        # Receive one update
        old_geometry = (10, 20, 30, 50)
        with self.reset_mock(mocked_send_changes):
            self.update_proxy(roi=old_geometry)
        self.assert_roi(roi=old_geometry)
        mocked_send_changes.assert_not_called()

        # Start user movement.
        roi = self.rois['roi']
        item = roi.roi_item
        with self.reset_mock(mocked_send_changes):
            item._moveStarted()
            with SignalBlocker(item):
                item.setPos((100, 300))
                item.setSize((100, 200))
            item.sigRegionChanged.emit(item)
        new_geometry = (100, 200, 300, 500)
        # Check if ROI has changed with the user changes
        self.assert_roi(roi=new_geometry)
        mocked_send_changes.assert_not_called()

        # Check if device changes are ignored when the ROI is moving
        newer_geometry = old_geometry
        with self.reset_mock(mocked_send_changes):
            self.update_proxy(roi=newer_geometry)
        self.assert_roi(roi=new_geometry)
        mocked_send_changes.assert_not_called()

        # Finish user movement
        with self.reset_mock(mocked_send_changes):
            with SignalBlocker(item):
                item.setPos((10, 30))
                item.setSize((10, 20))
            item.sigRegionChanged.emit(item)
            item._moveFinished()
        # Check if ROI has changed with the user changes
        self.assert_roi(roi=newer_geometry)
        mocked_send_changes.assert_called_once()

    # ---------------------------------------------------------------------
    # Helpers

    def update_proxy(self, **kwargs):
        geometries = self._values_cache
        if len(kwargs):
            geometries = kwargs
            self._values_cache.update(geometries)
        hsh = Hash({f'node.{key}': value
                    for key, value in geometries.items()})
        set_proxy_hash(self.proxy, hsh)

    def assert_roi(self, **kwargs):
        geometries = kwargs if len(kwargs) else self._values_cache
        for name, geometry in geometries.items():
            roi = self.rois[name]
            # Check traits
            assert roi.geometry == tuple(geometry)
            assert roi.is_visible is True
            # Check Qt item
            assert roi._item_geometry == roi.geometry
            assert roi.roi_item.isVisible() is roi.is_visible

    @property
    def widget(self):
        return self.controller.widget

    @property
    def rois(self):
        return {'roi': self.controller._roi}

    @contextmanager
    def reset_mock(self, mock_obj):
        mock_obj.reset_mock()
        yield
