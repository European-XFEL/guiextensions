import numpy as np
import pytest
from numpy.testing import assert_array_equal

from extensions.display_vector_graph_linear_regions import (
    DisplayVectorGraphWithLinearRegions, DisplayVectorXYGraphWithLinearRegions)
from karabo.native import (
    Configurable, Double, Int32, VectorDouble, VectorUInt32)
from karabogui.binding.api import (
    DeviceProxy, PropertyProxy, apply_default_configuration, build_binding)
from karabogui.testing import set_proxy_value

MODULE_PATH = "extensions.display_extended_vector_xy_graph"


class DeviceWithVectors(Configurable):
    x = VectorDouble()
    y = VectorDouble()
    lregion1 = VectorUInt32(defaultValue=[0, 10])
    lregion2 = VectorDouble(defaultValue=[20.0, 30.0])
    doubleProp = Double(defaultValue=0)
    intProp = Int32(defaultValue=0)


@pytest.fixture
def device_proxy(gui_app):
    schema = DeviceWithVectors.getClassSchema()
    binding = build_binding(schema)
    apply_default_configuration(binding)
    device = DeviceProxy(device_id="TestDevice",
                         server_id="TestServer",
                         binding=binding)
    return device


@pytest.fixture(name='proxies')
def property_proxies(device_proxy):
    properties = ['x', 'y',
                  'lregion1', 'lregion2',
                  'doubleProp', 'intProp']
    return {prop: PropertyProxy(root_proxy=device_proxy, path=prop)
            for prop in properties}


@pytest.fixture(name='vector_graph')
def vector_graph_with_linear_regions(proxies):
    controller = DisplayVectorGraphWithLinearRegions(proxy=proxies['y'])
    controller.create(None)
    _visualize_linear_regions(controller, proxies)

    yield controller
    controller.destroy()
    assert controller.widget is None


@pytest.fixture(name='vector_xy_graph')
def vector_xy_graph_with_linear_regions(proxies):
    controller = DisplayVectorXYGraphWithLinearRegions(proxy=proxies['x'])
    controller.create(None)
    controller.visualize_additional_property(proxies['y'])
    _visualize_linear_regions(controller, proxies)

    yield controller
    controller.destroy()
    assert controller.widget is None


def _visualize_linear_regions(controller, proxies):
    controller.visualize_additional_property(proxies['lregion1'])
    controller.visualize_additional_property(proxies['lregion2'])
    controller.visualize_additional_property(proxies['doubleProp'])
    controller.visualize_additional_property(proxies['intProp'])


def test_vector_graph_basics(vector_graph, proxies):
    x = np.arange(10)
    y = np.random.random(10)

    set_proxy_value(proxies['y'], 'y', y)
    curve = vector_graph._curves[proxies['y']]
    assert_array_equal(curve.xData, x)
    assert_array_equal(curve.yData, y)

    _assert_linear_regions(vector_graph, proxies)
    _assert_inf_lines(vector_graph, proxies)


def test_vector_xy_graph_basics(vector_xy_graph, proxies, mocker):
    x = np.arange(10)
    y = np.random.random(10)

    set_proxy_value(proxies['x'], 'x', x)
    set_proxy_value(proxies['y'], 'y', y)

    curve = vector_xy_graph._curves[proxies['y']]
    assert_array_equal(curve.xData, x)
    assert_array_equal(curve.yData, y)

    _assert_linear_regions(vector_xy_graph, proxies)
    _assert_inf_lines(vector_xy_graph, proxies)
    _assert_legends(vector_xy_graph, mocker)


def _assert_linear_regions(controller, proxies):
    set_proxy_value(proxies['lregion1'], "lregion1", [3, 7])
    set_proxy_value(proxies['lregion2'], "lregion2", [5.1, 8.5])

    lregion1 = controller._linear_regions[proxies['lregion1']]
    lregion2 = controller._linear_regions[proxies['lregion2']]

    assert_array_equal(lregion1.getRegion(), [3, 7])
    assert_array_equal(lregion2.getRegion(), [5.1, 8.5])


def _assert_inf_lines(controller, proxies):
    set_proxy_value(proxies['doubleProp'], "doubleProp", 4.56)
    set_proxy_value(proxies['intProp'], "intProp", 8)

    inf_line_1 = controller._inf_lines[proxies['doubleProp']]
    inf_line_2 = controller._inf_lines[proxies['intProp']]

    assert_array_equal(inf_line_1.value(), 4.56)
    assert_array_equal(inf_line_2.value(), 8)


def _assert_legends(controller, mocker):
    # Setup mocks
    config = {"names": ['y', 'lregion1', 'lregion2',
                        'doubleProp', 'intProp'],
              "legends": ['new y', 'new lregion1', 'new lregion2',
                          'new doubleProp', 'new intProp'],
              "removed": [False, False]}
    mocked_dialog = mocker.patch(f'{MODULE_PATH}.LegendTableDialog')
    mocked_dialog.get.return_value = (config, True)

    controller.configure_data()
    assert controller.model.legends == config["legends"]
    assert ([label.format for label in controller._linear_labels.values()]
            == ['new lregion1', 'new lregion2'])
