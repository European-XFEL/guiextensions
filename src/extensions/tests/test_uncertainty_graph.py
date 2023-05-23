import numpy as np
from numpy.testing import assert_array_equal

from karabo.native import (
    Configurable, Float, Hash, NDArray, Node, VectorDouble)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash, set_proxy_value)

from ..display_uncertainty_graph import UncertaintyGraph
from ..utils import get_ndarray_hash_from_data

SIZE = 10
X = np.arange(SIZE)
Y = np.random.rand(SIZE)
MEAN = np.random.rand(SIZE)
UNCERTAINTY = np.random.rand(SIZE) * 0.1


class VectorUncertaintyNode(Configurable):
    displayType = "WidgetNode|UncertaintyBand"

    mean = VectorDouble()
    uncertainty = VectorDouble()


class NdArrayUncertaintyNode(Configurable):
    displayType = "WidgetNode|UncertaintyBand"

    mean = NDArray(
        defaultValue=np.arange(2 * SIZE).reshape((2, SIZE)),
        shape=(2, SIZE),
        dtype=Float,)
    uncertainty = NDArray(
        defaultValue=np.arange(2 * SIZE).reshape((2, SIZE)),
        shape=(2, SIZE),
        dtype=Float,
    )


class ObjectNode(Configurable):
    x = VectorDouble()
    y = VectorDouble()
    vector = Node(VectorUncertaintyNode)
    ndarray = Node(NdArrayUncertaintyNode)


class TestUncertaintyGraph(GuiTestCase):
    def setUp(self):
        super(TestUncertaintyGraph, self).setUp()
        device = ObjectNode.getClassSchema()

        self.x_proxy = get_class_property_proxy(device, 'x')
        self.y_proxy = get_class_property_proxy(device, 'y')
        self.vector_unc_proxy = get_class_property_proxy(device, 'vector')
        self.ndarray_unc_proxy = get_class_property_proxy(device, 'ndarray')
        self.controller = UncertaintyGraph(proxy=self.x_proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    # ---------------------------------------------------------------------
    # Tests

    def test_empty(self):
        set_proxy_value(self.x_proxy, 'x', X)

        assert self.controller._unc_proxy is None
        mean = self.controller._unc_mean
        assert mean not in self.controller._curves.values()

        assert_array_equal(mean.xData, [])
        assert_array_equal(mean.yData, [])

        band = self.controller._unc_band
        assert_array_equal(band.curves, [[[], []], [[], []]])

    def test_1d_uncertainty_band(self):
        self.controller.visualize_additional_property(self.vector_unc_proxy)
        assert self.controller._unc_proxy is self.vector_unc_proxy
        mean = self.controller._unc_mean
        assert mean in self.controller._curves.values()

        # New data
        set_proxy_value(self.x_proxy, 'x', X)
        set_proxy_hash(self.vector_unc_proxy,
                       Hash("vector.mean", MEAN,
                            "vector.uncertainty", UNCERTAINTY))

        assert_array_equal(mean.xData, X)
        assert_array_equal(mean.yData, MEAN)

        band = self.controller._unc_band
        assert_array_equal(band.curves, [[X, MEAN-UNCERTAINTY],
                                         [X, MEAN+UNCERTAINTY]])

    def test_2d_uncertainty_band(self):
        self.controller.visualize_additional_property(self.ndarray_unc_proxy)
        assert self.controller._unc_proxy is self.ndarray_unc_proxy
        mean = self.controller._unc_mean
        assert mean in self.controller._curves.values()

        hsh = Hash(
            "ndarray.mean",
            get_ndarray_hash_from_data(np.array([MEAN, MEAN * 2])),
            "ndarray.uncertainty",
            get_ndarray_hash_from_data(np.array([UNCERTAINTY,
                                                 UNCERTAINTY * 2])))

        set_proxy_value(self.x_proxy, 'x', X)
        set_proxy_hash(self.ndarray_unc_proxy, hsh)

        assert_array_equal(mean.xData, X)
        assert_array_equal(mean.yData, MEAN)

        band = self.controller._unc_band
        assert_array_equal(band.curves, [[X, MEAN-UNCERTAINTY],
                                         [X, MEAN+UNCERTAINTY]])

    # ---------------------------------------------------------------------
    # Helpers

    @property
    def widget(self):
        return self.controller.widget
