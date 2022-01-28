from contextlib import contextmanager
from unittest import mock

import numpy as np

from extensions.metro.zone_plate import MetroZonePlate
from karabo.native import (
    Configurable, EncodingType, Hash, Image, ImageData, Node, VectorUInt32)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)
from karabogui.util import SignalBlocker


class ImageOutput(Configurable):
    image = Image(data=ImageData(np.zeros((100, 100), dtype=np.uint64),
                                 encoding=EncodingType.GRAY),
                  displayedName="Image")


class AggregatorNode(Configurable):
    paramRoiN = VectorUInt32(defaultValue=[])
    paramRoi0 = VectorUInt32(defaultValue=[])
    paramRoiP = VectorUInt32(defaultValue=[])
    outputImage = Node(ImageOutput)


class Object(Configurable):
    node = Node(AggregatorNode)


@mock.patch('extensions.display_roi_graph.send_property_changes')
@mock.patch.object(MetroZonePlate, '_set_image')
class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = MetroZonePlate(proxy=self.proxy)
        self.controller.create(None)

        self._values_cache = {
            'paramRoiN': [10, 20, 10, 20],
            'paramRoi0': [30, 50, 30, 50],
            'paramRoiP': [60, 90, 60, 90],
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

        # Check lines
        for name, lines in self.lines.items():
            for line in lines:
                assert line.value() == 0
                assert line.isVisible() is False

    def test_first_device_update(self, *mocks):
        # Mock receivng device update once
        self.update_proxy()

        self.assert_roi()
        self.assert_lines()

    def test_second_device_update(self, *mocks):
        # Mock receivng device update twice
        self.update_proxy()
        self.update_proxy(paramRoiN=(100, 200, 300, 500))

        self.assert_roi(paramRoiN=(100, 200, 300, 500))
        self.assert_lines(paramRoiN=(100, 200, 300, 500))

    def test_user_update(self, *mocks):
        # Receive one update
        old_geometry = (10, 20, 30, 50)
        self.update_proxy(paramRoiN=old_geometry)
        self.assert_roi(paramRoiN=old_geometry)
        self.assert_lines(paramRoiN=old_geometry)

        # Mock changes. Block signal on first change to trigger the ROI
        # movement only once, on the second change.
        roi = self.controller.roi_n
        item = roi.roi_item
        with SignalBlocker(item):
            item.setPos((100, 300))
        item.setSize((100, 200))
        # Check if ROI has changed with the user changes
        new_geometry = (100, 200, 300, 500)
        self.assert_roi(paramRoiN=new_geometry)
        self.assert_lines(paramRoiN=new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. Most probably it's still the old
        # value. We ignore the incoming data
        self.update_proxy(paramRoiN=old_geometry)
        self.assert_roi(paramRoiN=new_geometry)
        self.assert_lines(paramRoiN=new_geometry)
        assert roi.is_waiting is True

        # Receive an update from the device. The property has now ben updated.
        # value. We confirm that we are ready to receive new data.
        self.update_proxy(paramRoiN=new_geometry)
        self.assert_roi(paramRoiN=new_geometry)
        self.assert_lines(paramRoiN=new_geometry)
        assert roi.is_waiting is False

        # Receive an update from the device. A newer data has arrived.
        # value. We check if this will apply.
        newer_geometry = old_geometry
        self.update_proxy(paramRoiN=newer_geometry)
        self.assert_roi(paramRoiN=newer_geometry)
        self.assert_lines(paramRoiN=newer_geometry)
        assert roi.is_waiting is False

    def test_user_movement(self, _, mocked_send_changes):
        # Receive one update
        old_geometry = (10, 20, 30, 50)
        with self.reset_mock(mocked_send_changes):
            self.update_proxy(paramRoiN=old_geometry)
        self.assert_roi(paramRoiN=old_geometry)
        self.assert_lines(paramRoiN=old_geometry)
        mocked_send_changes.assert_not_called()

        # Start user movement.
        roi = self.controller.roi_n
        item = roi.roi_item
        with self.reset_mock(mocked_send_changes):
            item._moveStarted()
            with SignalBlocker(item):
                item.setPos((100, 300))
                item.setSize((100, 200))
            item.sigRegionChanged.emit(item)
        new_geomeetry = (100, 200, 300, 500)
        # Check if ROI has changed with the user changes
        self.assert_roi(paramRoiN=new_geomeetry)
        self.assert_lines(paramRoiN=new_geomeetry)
        mocked_send_changes.assert_not_called()

        # Check if device changes are ignored when the ROI is moving
        newer_geometry = old_geometry
        with self.reset_mock(mocked_send_changes):
            self.update_proxy(paramRoiN=newer_geometry)
        self.assert_roi(paramRoiN=new_geomeetry)
        self.assert_lines(paramRoiN=new_geomeetry)
        mocked_send_changes.assert_not_called()

        # Finish user movement
        with self.reset_mock(mocked_send_changes):
            with SignalBlocker(item):
                item.setPos((10, 30))
                item.setSize((10, 20))
            item.sigRegionChanged.emit(item)
            item._moveFinished()
        # Check if ROI has changed with the user changes
        self.assert_roi(paramRoiN=newer_geometry)
        self.assert_lines(paramRoiN=newer_geometry)
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

    def assert_lines(self, **kwargs):
        geometries = kwargs if len(kwargs) else self._values_cache
        for name, geometry in geometries.items():
            lines = self.lines[name]
            for line, value in zip(lines, geometry):
                assert line.value() == value

    @property
    def widget(self):
        return self.controller.widget

    @property
    def rois(self):
        controller = self.controller
        return {'paramRoiN': controller.roi_n,
                'paramRoi0': controller.roi_0,
                'paramRoiP': controller.roi_p}

    @property
    def lines(self):
        controller = self.controller
        return {'paramRoiN': controller._n_lines,
                'paramRoi0': controller._0_lines,
                'paramRoiP': controller._p_lines}

    @contextmanager
    def reset_mock(self, mock_obj):
        mock_obj.reset_mock()
        yield
