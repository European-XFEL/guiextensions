import numpy as np
from numpy.testing import assert_array_equal

from extensions.display_vector_graph_linear_regions import (
    DisplayVectorGraphWithLinearRegions)
from karabo.native import (
    Configurable, Double, Int32, VectorDouble, VectorUInt32)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)


def patched_send_property_changes(proxies):
    for proxy in proxies:
        set_proxy_value(proxy, proxy.path, proxy.edit_value)


class DeviceWithVectors(Configurable):
    data = VectorDouble()
    lregion1 = VectorUInt32()
    lregion2 = VectorDouble()
    doubleProp = Double(defaultValue=0)
    intProp = Int32(defaultValue=0)


class VectorGraphWithLinearRegionsTest(GuiTestCase):

    def setUp(self):
        super(VectorGraphWithLinearRegionsTest, self).setUp()

        schema = DeviceWithVectors.getClassSchema()

        self.data_proxy = get_class_property_proxy(schema, 'data')
        self.lregion1_proxy = get_class_property_proxy(schema, "lregion1")
        self.lregion2_proxy = get_class_property_proxy(schema, "lregion2")
        self.double_prop_proxy = get_class_property_proxy(schema, "doubleProp")
        self.int_prop_proxy = get_class_property_proxy(schema, "intProp")

        self.controller = DisplayVectorGraphWithLinearRegions(
            proxy=self.data_proxy)
        self.controller.create(None)
        self.controller.visualize_additional_property(self.lregion1_proxy)
        self.controller.visualize_additional_property(self.lregion2_proxy)
        self.controller.visualize_additional_property(self.double_prop_proxy)
        self.controller.visualize_additional_property(self.int_prop_proxy)

    def tearDown(self):
        super(VectorGraphWithLinearRegionsTest, self).tearDown()
        self.controller.destroy()

    def test_basics(self):
        x = np.arange(10)
        y = np.random.random(10)

        set_proxy_value(self.data_proxy, "data", y)
        curve = self.controller._curves[self.data_proxy]
        assert_array_equal(curve.xData, x)
        assert_array_equal(curve.yData, y)

        set_proxy_value(self.lregion1_proxy, "lregion1", [3, 7])
        set_proxy_value(self.lregion2_proxy, "lregion2", [5.1, 8.5])

        lregion1 = self.controller._linear_regions[self.lregion1_proxy]
        lregion2 = self.controller._linear_regions[self.lregion2_proxy]

        assert_array_equal(lregion1.getRegion(), [3, 7])
        assert_array_equal(lregion2.getRegion(), [5.1, 8.5])

        set_proxy_value(self.double_prop_proxy, "doubleProp", 4.56)
        set_proxy_value(self.int_prop_proxy, "intProp", 8)

        inf_line_1 = self.controller._inf_lines[self.double_prop_proxy]
        inf_line_2 = self.controller._inf_lines[self.int_prop_proxy]

        assert_array_equal(inf_line_1.value(), 4.56)
        assert_array_equal(inf_line_2.value(), 8)
