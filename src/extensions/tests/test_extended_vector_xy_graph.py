from unittest import mock

import numpy as np
from numpy.testing import assert_array_equal

from extensions.display_extended_vector_xy_graph import (
    DisplayExtendedVectorXYGraph, EditableTableVectorXYGraph)
from karabo.native import Configurable, Hash, String, VectorHash, VectorUInt32
from karabogui.binding.api import (
    DeviceProxy, PropertyProxy, ProxyStatus, build_binding)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)

MODULE_PATH = "extensions.display_extended_vector_xy_graph"


def patched_send_property_changes(proxies):
    for proxy in proxies:
        set_proxy_value(proxy, proxy.path, proxy.edit_value)


class DeviceWithVectors(Configurable):
    x = VectorUInt32()
    y0 = VectorUInt32()
    y1 = VectorUInt32()


class Base(GuiTestCase):

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


class BaseExtendedVectorXYGraphTest(Base):

    def setUp(self):
        super(Base, self).setUp()

        schema = DeviceWithVectors.getClassSchema()
        self.x_proxy = get_class_property_proxy(schema, 'x')
        self.y0_proxy = get_class_property_proxy(schema, 'y0')
        self.y1_proxy = get_class_property_proxy(schema, 'y1')

        self.controller = DisplayExtendedVectorXYGraph(proxy=self.x_proxy)
        self.controller.create(None)
        self.controller.visualize_additional_property(self.y0_proxy)
        self.controller.visualize_additional_property(self.y1_proxy)


class TestCurves(BaseExtendedVectorXYGraphTest):

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


@mock.patch(f'{MODULE_PATH}.LegendTableDialog')
class TestLegends(BaseExtendedVectorXYGraphTest):

    def test_basics(self, mocked_dialog):
        self.assertListEqual(self.model.legends, ['', ''])

    def test_first_call(self, mocked_dialog):
        # Return intermittently
        mocked_dialog.get.return_value = (None, False)

        self.controller.configure_data()
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

        self.controller.configure_data()
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
        self.controller.configure_data()

        # Second call: return intermittently
        mocked_dialog.reset_mock()
        mocked_dialog.get.return_value = (None, False)
        self.controller.configure_data()
        mocked_dialog.get.assert_called_with(
            {"names": ['y0', 'y1'],
             "legends": ['foo', 'bar'],
             "removable": [False, False]},
            parent=self.controller.widget)


FIRST_ARRAY = np.vstack((np.arange(10), np.arange(10) ** 2))
SECOND_ARRAY = np.vstack((np.arange(10, 20), np.arange(10, 20) ** 2))


@mock.patch(f'{MODULE_PATH}.LegendTableDialog')
@mock.patch(f'{MODULE_PATH}.getOpenFileName')
class TestPersistentData(BaseExtendedVectorXYGraphTest):

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


# -----------------------------------------------------------------------------
# Table Vector XY Graph tests

class TableSchema(Configurable):
    label = String()
    x = VectorUInt32()
    y = VectorUInt32()


class DeviceWithTable(Configurable):
    prop = VectorHash(rows=TableSchema)


class BaseTableVectorXYGraphTest(Base):
    """"""

    def setUp(self):
        super(Base, self).setUp()
        schema = DeviceWithTable.getClassSchema()
        binding = build_binding(schema)
        root_proxy = DeviceProxy(binding=binding, device_id='TestDevice')
        root_proxy.status = ProxyStatus.ONLINE
        self.prop_proxy = PropertyProxy(root_proxy=root_proxy, path='prop')

        self.controller = EditableTableVectorXYGraph(proxy=self.prop_proxy)
        self.controller.create(None)

    def set_table(self, **rows):
        table = [Hash('label', label, 'x', values[0], 'y', values[1])
                 for label, values in rows.items()]
        set_proxy_value(self.prop_proxy, 'prop', table)


class TestTableVectorXYGraph(BaseTableVectorXYGraphTest):
    def test_basics(self):
        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]))
        assert len(self.controller._curves) == 2

        first = self.controller._curves['first']
        assert_array_equal(first.xData, [0, 1, 2, 3, 4])
        assert_array_equal(first.yData, [5, 6, 7, 8, 9])

        second = self.controller._curves['second']
        assert_array_equal(second.xData, [10, 11, 12, 13])
        assert_array_equal(second.yData, [14, 15, 16, 17])

    def test_empty(self):
        assert len(self.controller._curves) == 0

    def test_add_rows(self):
        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]))
        assert len(self.controller._curves) == 2

        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]),
                       third=np.array([[20, 21, 22, 23],
                                       [24, 25, 26, 27]]))
        assert len(self.controller._curves) == 3

        first = self.controller._curves['first']
        assert_array_equal(first.xData, [0, 1, 2, 3, 4])
        assert_array_equal(first.yData, [5, 6, 7, 8, 9])

        second = self.controller._curves['second']
        assert_array_equal(second.xData, [10, 11, 12, 13])
        assert_array_equal(second.yData, [14, 15, 16, 17])

        third = self.controller._curves['third']
        assert_array_equal(third.xData, [20, 21, 22, 23])
        assert_array_equal(third.yData, [24, 25, 26, 27])

    def test_remove_rows(self):
        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]))
        assert len(self.controller._curves) == 2

        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]))
        assert len(self.controller._curves) == 1

        first = self.controller._curves['first']
        assert_array_equal(first.xData, [0, 1, 2, 3, 4])
        assert_array_equal(first.yData, [5, 6, 7, 8, 9])

    def test_configure_data(self):
        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]))


@mock.patch(f'{MODULE_PATH}.send_property_changes',
            new=patched_send_property_changes)
@mock.patch(f'{MODULE_PATH}.LegendTableDialog')
class TestConfigureTableVectorXYGraph(BaseTableVectorXYGraphTest):

    def test_rename(self, mocked_dialog, *_):
        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]))
        assert len(self.controller._curves) == 2

        config = {"names": ['first', 'second'],
                  "legends": ['firsty', 'secondy'],
                  "removed": [False, False]}
        mocked_dialog.get.return_value = (config, True)
        self.controller.configure_data()

        mocked_dialog.get.assert_called_with(
            {"names": ['first', 'second'],
             "legends": ['first', 'second'],
             "removable": [True, True]},
            parent=self.controller.widget
        )
        assert len(self.controller._curves) == 2

        first = self.controller._curves['firsty']
        assert_array_equal(first.xData, [0, 1, 2, 3, 4])
        assert_array_equal(first.yData, [5, 6, 7, 8, 9])

        second = self.controller._curves['secondy']
        assert_array_equal(second.xData, [10, 11, 12, 13])
        assert_array_equal(second.yData, [14, 15, 16, 17])

    def test_remove(self, mocked_dialog, *_):
        self.set_table(first=np.array([[0, 1, 2, 3, 4],
                                       [5, 6, 7, 8, 9]]),
                       second=np.array([[10, 11, 12, 13],
                                       [14, 15, 16, 17]]))
        assert len(self.controller._curves) == 2

        config = {"names": ['first', 'second'],
                  "legends": ['first', 'second'],
                  "removed": [True, False]}
        mocked_dialog.get.return_value = (config, True)
        self.controller.configure_data()

        mocked_dialog.get.assert_called_with(
            {"names": ['first', 'second'],
             "legends": ['first', 'second'],
             "removable": [True, True]},
            parent=self.controller.widget
        )
        assert len(self.controller._curves) == 1

        second = self.controller._curves['second']
        assert_array_equal(second.xData, [10, 11, 12, 13])
        assert_array_equal(second.yData, [14, 15, 16, 17])


class TablePlotTypeSchema(Configurable):
    label = String()
    x = VectorUInt32()
    y = VectorUInt32()
    plotType = String()


class DeviceWithTablePlotType(Configurable):
    prop = VectorHash(rows=TablePlotTypeSchema)


class TestPlotTypeTableVectorXYGraph(Base):
    """"""

    def setUp(self):
        super(Base, self).setUp()
        schema = DeviceWithTablePlotType.getClassSchema()
        binding = build_binding(schema)
        root_proxy = DeviceProxy(binding=binding, device_id='TestDevice')
        root_proxy.status = ProxyStatus.ONLINE
        self.prop_proxy = PropertyProxy(root_proxy=root_proxy, path='prop')

        self.controller = EditableTableVectorXYGraph(proxy=self.prop_proxy)
        self.controller.create(None)

    def test_basics(self):
        # Send two scatters, one line data
        first_data = [
            Hash('label', 'scatter 1',
                 'x', np.arange(5),
                 'y', np.arange(5) * 2,
                 'plotType', 'scatter'),
            Hash('label', 'scatter 2',
                 'x', np.arange(10),
                 'y', np.arange(10) * 2,
                 'plotType', 'scatter'),
            Hash('label', 'line 1',
                 'x', np.arange(15),
                 'y', np.arange(15) * 2,
                 'plotType', 'line'),
        ]
        set_proxy_value(self.prop_proxy, 'prop', first_data)
        assert len(self.controller._scatters) == 2
        assert len(self.controller._curves) == 1

        # Check data
        scatter_1 = self.controller._scatters['scatter 1']
        assert_array_equal(scatter_1.data['x'], np.arange(5))
        assert_array_equal(scatter_1.data['y'], np.arange(5) * 2)

        scatter_2 = self.controller._scatters['scatter 2']
        assert_array_equal(scatter_2.data['x'], np.arange(10))
        assert_array_equal(scatter_2.data['y'], np.arange(10) * 2)

        line_1 = self.controller._curves['line 1']
        assert_array_equal(line_1.xData, np.arange(15))
        assert_array_equal(line_1.yData, np.arange(15) * 2)

    def test_same_change(self):
        first_data = [
            Hash('label', 'scatter 1 bad',
                 'x', np.random.randint(10, size=5),
                 'y', np.random.randint(10, size=5),
                 'plotType', 'scatter'),
            Hash('label', 'line 1 bad',
                 'x', np.random.randint(10, size=5),
                 'y', np.random.randint(10, size=5),
                 'plotType', 'line'),
            Hash('label', 'line 2 bad',
                 'x', np.random.randint(10, size=5),
                 'y', np.random.randint(10, size=5),
                 'plotType', 'line'),
        ]
        set_proxy_value(self.prop_proxy, 'prop', first_data)

        second_data = [
            Hash('label', 'scatter 1',
                 'x', np.arange(5),
                 'y', np.arange(5) * 2,
                 'plotType', 'scatter'),
            Hash('label', 'scatter 2',
                 'x', np.arange(10),
                 'y', np.arange(10) * 2,
                 'plotType', 'scatter'),
            Hash('label', 'line 1',
                 'x', np.arange(15),
                 'y', np.arange(15) * 2,
                 'plotType', 'line'),
        ]
        set_proxy_value(self.prop_proxy, 'prop', second_data)
        assert len(self.controller._scatters) == 2
        assert len(self.controller._curves) == 1

        # Check data
        scatter_1 = self.controller._scatters['scatter 1']
        assert_array_equal(scatter_1.data['x'], np.arange(5))
        assert_array_equal(scatter_1.data['y'], np.arange(5) * 2)

        scatter_2 = self.controller._scatters['scatter 2']
        assert_array_equal(scatter_2.data['x'], np.arange(10))
        assert_array_equal(scatter_2.data['y'], np.arange(10) * 2)

        line_1 = self.controller._curves['line 1']
        assert_array_equal(line_1.xData, np.arange(15))
        assert_array_equal(line_1.yData, np.arange(15) * 2)

    def test_different_change(self):
        first_data = [
            Hash('label', 'scatter 1 bad',
                 'x', np.random.randint(10, size=5),
                 'y', np.random.randint(10, size=5),
                 'plotType', 'scatter'),
            Hash('label', 'line 1 bad',
                 'x', np.random.randint(10, size=5),
                 'y', np.random.randint(10, size=5),
                 'plotType', 'line'),
            Hash('label', 'line 2 bad',
                 'x', np.random.randint(10, size=5),
                 'y', np.random.randint(10, size=5),
                 'plotType', 'line'),
        ]
        set_proxy_value(self.prop_proxy, 'prop', first_data)

        second_data = [
            Hash('label', 'scatter 1',
                 'x', np.arange(5),
                 'y', np.arange(5) * 2,
                 'plotType', 'scatter'),
            Hash('label', 'scatter 2',
                 'x', np.arange(10),
                 'y', np.arange(10) * 2,
                 'plotType', 'scatter'),
            Hash('label', 'line 1',
                 'x', np.arange(15),
                 'y', np.arange(15) * 2,
                 'plotType', 'line'),
        ]
        set_proxy_value(self.prop_proxy, 'prop', second_data)
        assert len(self.controller._scatters) == 2
        assert len(self.controller._curves) == 1

        # Check data
        scatter_1 = self.controller._scatters['scatter 1']
        assert_array_equal(scatter_1.data['x'], np.arange(5))
        assert_array_equal(scatter_1.data['y'], np.arange(5) * 2)

        scatter_2 = self.controller._scatters['scatter 2']
        assert_array_equal(scatter_2.data['x'], np.arange(10))
        assert_array_equal(scatter_2.data['y'], np.arange(10) * 2)

        line_1 = self.controller._curves['line 1']
        assert_array_equal(line_1.xData, np.arange(15))
        assert_array_equal(line_1.yData, np.arange(15) * 2)

    def test_invalid_plottype(self):
        # Send two scatters, one line data
        first_data = [
            Hash('label', 'scatter 1',
                 'x', np.arange(5),
                 'y', np.arange(5) * 2,
                 'plotType', 'bad scatter'),
            Hash('label', 'scatter 2',
                 'x', np.arange(10),
                 'y', np.arange(10) * 2,
                 'plotType', 'badScatter'),
            Hash('label', 'line 1',
                 'x', np.arange(15),
                 'y', np.arange(15) * 2,
                 'plotType', 'badLine'),
        ]
        set_proxy_value(self.prop_proxy, 'prop', first_data)
        assert len(self.controller._scatters) == 0
        assert len(self.controller._curves) == 3

        # Check data
        scatter_1 = self.controller._curves['scatter 1']
        assert_array_equal(scatter_1.xData, np.arange(5))
        assert_array_equal(scatter_1.yData, np.arange(5) * 2)

        scatter_2 = self.controller._curves['scatter 2']
        assert_array_equal(scatter_2.xData, np.arange(10))
        assert_array_equal(scatter_2.yData, np.arange(10) * 2)

        line_1 = self.controller._curves['line 1']
        assert_array_equal(line_1.xData, np.arange(15))
        assert_array_equal(line_1.yData, np.arange(15) * 2)
