from extensions.display_two_axis_graph import DisplayXYTwoAxisGraph
from karabo.native import Configurable, VectorDouble
from karabogui.api import get_pen_cycler
from karabogui.testing import get_class_property_proxy, set_proxy_value


class TestDevice(Configurable):
    first_data = VectorDouble()
    second_data = VectorDouble()
    third_data = VectorDouble()


def test_controller(gui_app, mocker):

    schema = TestDevice.getClassSchema()
    proxy = get_class_property_proxy(schema, "first_data")
    value = [1.0, 2.0, 3.0, 4.0, 5.0]
    set_proxy_value(proxy, "first_data", value)
    controller = DisplayXYTwoAxisGraph(proxy=proxy)
    controller.create(None)

    widget = controller.widget
    plot_item = widget.plotItem
    assert not controller._curves.data
    assert not plot_item.legend.isVisible()
    assert controller.proxy

    # Add another proxy - Left Y-axis data
    second_proxy = get_class_property_proxy(schema, "second_data")
    set_proxy_value(proxy, "second_data", [9.1, 5.2, 2.4, 2.8])
    assert controller.visualize_additional_property(second_proxy)
    assert len(controller._curves) == 1
    assert second_proxy in controller._curves
    assert plot_item.legend.isVisible()

    left_axis = plot_item.getAxis("left")
    right_axis = plot_item.getAxis("right")
    pen_cycler = get_pen_cycler()
    left_pen = next(pen_cycler)
    left_color = left_axis.pen().color().name()
    assert left_pen.color().name() == left_color

    # Add Right Y-axis data
    third_proxy = get_class_property_proxy(schema, "third_data")
    set_proxy_value(proxy, "third_data", [10.0, 20.0, 30.0, 40.0])
    assert controller.visualize_additional_property(third_proxy)
    assert len(controller._curves) == 2

    # Remove left Y-axis data
    assert controller.remove_additional_property(second_proxy)
    assert len(controller._curves) == 1

    # Remove right Y-axis data
    assert controller.remove_additional_property(third_proxy)
    assert third_proxy not in controller._curves
    color = right_axis.pen().color().name()
    default_color = plot_item.getAxis("top").pen().color().name()
    assert default_color == color
    assert len(controller._curves) == 0
