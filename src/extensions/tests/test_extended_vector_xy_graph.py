from unittest import mock

import numpy as np

from extensions.display_extended_vector_xy_graph import (
    DisplayExtendedVectorXYGraph)
from karabo.native import Configurable, VectorUInt32
from karabogui.testing import GuiTestCase, get_class_property_proxy


class Object(Configurable):
    x = VectorUInt32()
    y0 = VectorUInt32()
    y1 = VectorUInt32()


class Base(GuiTestCase):
    def setUp(self):
        super(Base, self).setUp()

        schema = Object.getClassSchema()
        self.x_proxy = get_class_property_proxy(schema, 'x')
        self.y0_proxy = get_class_property_proxy(schema, 'y0')
        self.y1_proxy = get_class_property_proxy(schema, 'y1')

        self.controller = DisplayExtendedVectorXYGraph(proxy=self.x_proxy)
        self.controller.create(None)
        self.controller.visualize_additional_property(self.y0_proxy)
        self.controller.visualize_additional_property(self.y1_proxy)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    @property
    def model(self):
        return self.controller.model

    @property
    def plotItem(self):
        return self.controller.widget.plotItem

    @property
    def legend_item(self):
        return self.plotItem.legend


@mock.patch('extensions.display_extended_vector_xy_graph.LegendTableDialog')
class TestLegends(Base):

    def test_basics(self, mocked_dialog):
        self.assertListEqual(self.model.legends, ['', ''])

    def test_first_call(self, mocked_dialog):
        # Return intermittently
        mocked_dialog.get.return_value = (None, False)

        self.controller._configure_legends()
        mocked_dialog.get.assert_called_with(
            {"proxies": ['y0', 'y1'],
             "legends": ['', '']},
            parent=self.controller.widget
        )

    def test_first_update(self, mocked_dialog):
        # Return with proper value
        config = {"proxies": ['y0', 'y1'], "legends": ['foo', 'bar']}
        mocked_dialog.get.return_value = (config, True)

        self.controller._configure_legends()
        self.assertListEqual(self.model.legends, config["legends"])
        zipped = zip((self.y0_proxy, self.y1_proxy), config["legends"])
        for proxy, legend in zipped:
            curve = self.controller._curves[proxy]
            self.assertEqual(curve.name(), legend)
            self.assertEqual(self.legend_item.getLabel(curve).text, legend)

    def test_second_call(self, mocked_dialog):
        # First call: return with initial value
        config = {"proxies": ['y0', 'y1'], "legends": ['foo', 'bar']}
        mocked_dialog.get.return_value = (config, True)
        self.controller._configure_legends()

        # Second call: return intermittently
        mocked_dialog.reset_mock()
        mocked_dialog.get.return_value = (None, False)
        self.controller._configure_legends()
        mocked_dialog.get.assert_called_with(config,
                                             parent=self.controller.widget)


FIRST_ARRAY = np.vstack((np.arange(10), np.arange(10) ** 2))
SECOND_ARRAY = np.vstack((np.arange(10, 20), np.arange(10, 20) ** 2))


@mock.patch('extensions.display_extended_vector_xy_graph.getOpenFileName')
class TestPersistentData(Base):

    def test_basics(self, mocked_dialog):
        assert len(self.controller._persistent_curves) == 0

    def test_first_load_one_array(self, mocked_dialog):
        mocked_dialog.return_value = "foo.npy"
        with mock.patch.object(np, 'load', return_value=FIRST_ARRAY):
            self.controller._load_persistent_data()

        assert len(self.persistent_curves) == 1
        for curve, array in zip(self.persistent_curves, (FIRST_ARRAY,)):
            assert curve in self.plotItem.items
            np.testing.assert_array_equal(curve.xData, array[0])
            np.testing.assert_array_equal(curve.yData, array[1])

    def test_first_load_two_arrays(self, mocked_dialog):
        mocked_dialog.return_value = "foo.npz"
        mocked_npz = self._mock_npz(first_array=FIRST_ARRAY,
                                     second_array=SECOND_ARRAY)
        with mock.patch.object(np, 'load', return_value=mocked_npz):
            self.controller._load_persistent_data()

        assert len(self.persistent_curves) == 2
        zipped = zip(self.persistent_curves, (FIRST_ARRAY, SECOND_ARRAY))
        for curve, array in zipped:
            assert curve in self.plotItem.items
            np.testing.assert_array_equal(curve.xData, array[0])
            np.testing.assert_array_equal(curve.yData, array[1])

    def test_first_load_clear(self, mocked_dialog):
        mocked_dialog.return_value = "foo.npy"
        with mock.patch.object(np, 'load', return_value=FIRST_ARRAY):
            self.controller._load_persistent_data()
        self.controller._clear_persistent_data()

        assert len(self.persistent_curves) == 1
        for curve in self.persistent_curves:
            assert curve not in self.plotItem.items

    def test_second_load(self, mocked_dialog):
        # Load two arrays
        mocked_dialog.return_value = "foo.npz"
        mocked_npz = self._mock_npz(first_array=FIRST_ARRAY,
                                     second_array=SECOND_ARRAY)
        with mock.patch.object(np, 'load', return_value=mocked_npz):
            self.controller._load_persistent_data()

        # Load one array
        mocked_dialog.return_value = "foo.npy"
        with mock.patch.object(np, 'load', return_value=FIRST_ARRAY):
            self.controller._load_persistent_data()
        assert len(self.persistent_curves) == 2
        for curve, array in zip(self.persistent_curves[:1], (FIRST_ARRAY,)):
            assert curve in self.plotItem.items
            np.testing.assert_array_equal(curve.xData, array[0])
            np.testing.assert_array_equal(curve.yData, array[1])
        for curve in self.persistent_curves[1:]:
            assert curve not in self.plotItem.items

    @staticmethod
    def _mock_npz( **data):
        mocked_npz = mock.MagicMock()
        mocked_npz.items.side_effect = data.items
        mocked_npz.__len__.side_effect = data.__len__
        return mocked_npz

    @property
    def persistent_curves(self):
        return self.controller._persistent_curves