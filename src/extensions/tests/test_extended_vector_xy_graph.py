from unittest import mock

import numpy as np
from numpy.testing import assert_array_equal

from extensions.display_extended_vector_xy_graph import (
    DisplayExtendedVectorXYGraph)
from karabo.native import Configurable, VectorUInt32
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)


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


class TestCurves(Base):

    def test_basics(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', x)
        set_proxy_value(self.y0_proxy, 'y0', x * 2)
        set_proxy_value(self.y1_proxy, 'y1', x * 3)

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, x)
        assert_array_equal(y0_curve.yData, x * 2)

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, x)
        assert_array_equal(y1_curve.yData, x * 3)

    def test_longer_y0(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', x)
        set_proxy_value(self.y0_proxy, 'y0', np.arange(11) * 2)
        set_proxy_value(self.y1_proxy, 'y1', x * 3)

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, x)
        assert_array_equal(y0_curve.yData, x * 2)

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, x)
        assert_array_equal(y1_curve.yData, x * 3)

    def test_longer_y1(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', x)
        set_proxy_value(self.y0_proxy, 'y0', x * 2)
        set_proxy_value(self.y1_proxy, 'y1', np.arange(11) * 3)

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, x)
        assert_array_equal(y0_curve.yData, x * 2)

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, x)
        assert_array_equal(y1_curve.yData, x * 3)

    def test_longer_x(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', np.arange(11))
        set_proxy_value(self.y0_proxy, 'y0', x * 2)
        set_proxy_value(self.y1_proxy, 'y1', x * 3)

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, x)
        assert_array_equal(y0_curve.yData, x * 2)

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, x)
        assert_array_equal(y1_curve.yData, x * 3)

    def test_empty_y0(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', x)
        set_proxy_value(self.y0_proxy, 'y0', np.array([]))
        set_proxy_value(self.y1_proxy, 'y1', x * 3)

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, [])
        assert_array_equal(y0_curve.yData, [])

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, x)
        assert_array_equal(y1_curve.yData, x * 3)

    def test_empty_y1(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', x)
        set_proxy_value(self.y0_proxy, 'y0', x * 2)
        set_proxy_value(self.y1_proxy, 'y1', np.array([]))

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, x)
        assert_array_equal(y0_curve.yData, x * 2)

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, [])
        assert_array_equal(y1_curve.yData, [])

    def test_empty_x(self):
        x = np.arange(10)
        set_proxy_value(self.x_proxy, 'x', np.array([]))
        set_proxy_value(self.y0_proxy, 'y0', x * 2)
        set_proxy_value(self.y1_proxy, 'y1', x * 3)

        y0_curve = self.controller._curves[self.y0_proxy]
        assert_array_equal(y0_curve.xData, [])
        assert_array_equal(y0_curve.yData, [])

        y1_curve = self.controller._curves[self.y1_proxy]
        assert_array_equal(y1_curve.xData, [])
        assert_array_equal(y1_curve.yData, [])


@mock.patch('extensions.display_extended_vector_xy_graph.LegendTableDialog')
class TestLegends(Base):

    def test_basics(self, mocked_dialog):
        self.assertListEqual(self.model.legends, ['', ''])

    def test_first_call(self, mocked_dialog):
        # Return intermittently
        mocked_dialog.get.return_value = (None, False)

        self.controller._configure_data()
        mocked_dialog.get.assert_called_with(
            {"names": ['y0', 'y1'],
             "legends": ['', ''],
             "removable": [False, False]},
            parent=self.controller.widget
        )

    def test_first_update(self, mocked_dialog):
        # Return with proper value
        config = {"names": ['y0', 'y1'],
                  "legends": ['foo', 'bar'],
                  "removed": [False, False]}
        mocked_dialog.get.return_value = (config, True)

        self.controller._configure_data()
        self.assertListEqual(self.model.legends, config["legends"])
        zipped = zip((self.y0_proxy, self.y1_proxy), config["legends"])
        for proxy, legend in zipped:
            curve = self.controller._curves[proxy]
            self.assertEqual(curve.name(), legend)
            self.assertEqual(self.legend_item.getLabel(curve).text, legend)

    def test_second_call(self, mocked_dialog):
        # First call: return with initial value
        config = {"names": ['y0', 'y1'],
                  "legends": ['foo', 'bar'],
                  "removed": [False, False]}
        mocked_dialog.get.return_value = (config, True)
        self.controller._configure_data()

        # Second call: return intermittently
        mocked_dialog.reset_mock()
        mocked_dialog.get.return_value = (None, False)
        self.controller._configure_data()
        mocked_dialog.get.assert_called_with(
            {"names": ['y0', 'y1'],
             "legends": ['foo', 'bar'],
             "removable": [False, False]},
            parent=self.controller.widget)


FIRST_ARRAY = np.vstack((np.arange(10), np.arange(10) ** 2))
SECOND_ARRAY = np.vstack((np.arange(10, 20), np.arange(10, 20) ** 2))


@mock.patch('extensions.display_extended_vector_xy_graph.LegendTableDialog')
@mock.patch('extensions.display_extended_vector_xy_graph.getOpenFileName')
class TestPersistentData(Base):

    def test_basics(self, *_):
        assert len(self.controller._persistent_curves) == 0

    def test_first_load_one_array(self, openfilename, *_):
        openfilename.return_value = "foo.npy"

        with mock.patch.object(np, 'load', return_value=FIRST_ARRAY):
            self.controller._load_persistent_data()

        assert len(self.persistent_curves) == 1
        names, curves = zip(*self.persistent_curves)
        zipped = zip(names, curves, (FIRST_ARRAY,))
        for name, curve, array in zipped:
            assert curve in self.plotItem.items
            assert curve.name() == name
            np.testing.assert_array_equal(curve.xData, array[0])
            np.testing.assert_array_equal(curve.yData, array[1])

    def test_first_load_two_arrays(self, openfilename, legendtabledialog):
        openfilename.return_value = "foo.npz"
        legendtabledialog.get.return_value = ({
            "names": ['first_array', 'second_array'],
            "legends": ['', ''],
            "removed": [False, False]}, True)

        mocked_npz = self._mock_npz(first_array=FIRST_ARRAY,
                                    second_array=SECOND_ARRAY)
        with mock.patch.object(np, 'load', return_value=mocked_npz):
            self.controller._load_persistent_data()

        assert len(self.persistent_curves) == 2
        zipped = zip(self.persistent_curves, (FIRST_ARRAY, SECOND_ARRAY))
        for (name, curve), array in zipped:
            assert curve in self.plotItem.items
            assert curve.name() == name
            np.testing.assert_array_equal(curve.xData, array[0])
            np.testing.assert_array_equal(curve.yData, array[1])

    def test_first_load_clear(self, openfilename, legendtabledialog):
        openfilename.return_value = "foo.npy"
        legendtabledialog.get.return_value = {
            "names": ['first_array'],
            "legends": [''],
            "removed": [False]}

        with mock.patch.object(np, 'load', return_value=FIRST_ARRAY):
            self.controller._load_persistent_data()
        self.controller._clear_persistent_data()

        assert len(self.persistent_curves) == 0
        for curve in self.persistent_curves:
            assert curve not in self.plotItem.items

    def test_second_load(self, mocked_openfilename, legendtabledialog):
        # Load two arrays
        mocked_openfilename.return_value = "foo.npz"
        legendtabledialog.get.return_value = ({
            "names": ['first_array', 'second_array'],
            "legends": ['', ''],
            "removed": [False, False]}, True)
        mocked_npz = self._mock_npz(first_array=FIRST_ARRAY,
                                    second_array=SECOND_ARRAY)
        with mock.patch.object(np, 'load', return_value=mocked_npz):
            self.controller._load_persistent_data()

        # Load one array
        mocked_openfilename.return_value = "foo.npy"
        with mock.patch.object(np, 'load', return_value=FIRST_ARRAY):
            self.controller._load_persistent_data()
        assert len(self.persistent_curves) == 3
        zipped = zip(self.persistent_curves[2:], (FIRST_ARRAY,))
        for (name, curve), array in zipped:
            assert curve in self.plotItem.items
            np.testing.assert_array_equal(curve.xData, array[0])
            np.testing.assert_array_equal(curve.yData, array[1])
        for curve in self.persistent_curves[1:]:
            assert curve not in self.plotItem.items

    @staticmethod
    def _mock_npz(**data):
        mocked_npz = mock.MagicMock()
        mocked_npz.keys.side_effect = data.keys
        mocked_npz.items.side_effect = data.items
        mocked_npz.__len__.side_effect = data.__len__
        mocked_npz.__getitem__.side_effect = data.__getitem__
        return mocked_npz

    @property
    def persistent_curves(self):
        return self.controller._persistent_curves
