import pytest

from extensions.display_dynamic_graph import DisplayDynamicGraph
from extensions.models.plots import DynamicGraphModel
from karabo.native import AccessMode, Configurable, VectorDouble
from karabogui.testing import get_class_property_proxy, set_proxy_value


class Object(Configurable):
    prop = VectorDouble(
        defaultValue=[1.0, 2.0],
        accessMode=AccessMode.READONLY)


@pytest.fixture()
def controller_widget(gui_app):
    schema = Object.getClassSchema()
    proxy = get_class_property_proxy(schema, "prop")
    controller = DisplayDynamicGraph(proxy=proxy)
    controller.create(None)
    yield controller

    controller.destroy()
    assert controller.widget is None


def test_set_value(controller_widget):
    proxy = controller_widget.proxy
    assert len(controller_widget.curves) == 10
    curve = controller_widget.curves[0]
    assert curve is not None
    value = [2, 4, 6]
    set_proxy_value(proxy, "prop", value)
    assert list(curve.yData) == value


def test_actions(controller_widget, mocker):
    proxy = controller_widget.proxy
    controller = DisplayDynamicGraph(proxy=proxy,
                                     model=DynamicGraphModel())
    controller.create(None)
    assert len(controller.widget.actions()) >= 11
    action = None
    for ac in controller.widget.actions():
        if ac.text() == "Number of Curves":
            action = ac
            break
    assert action is not None
    assert controller.model.number == 10
    assert len(controller.curves) == 10
    dsym = 'extensions.display_dynamic_graph.QInputDialog'
    QInputDialog = mocker.patch(dsym)
    QInputDialog.getInt.return_value = 12, True
    action.trigger()
    assert controller.model.number == 12
    assert len(controller.curves) == 12

    controller.destroy()
