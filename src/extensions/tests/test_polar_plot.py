import numpy as np

from extensions.display_polar_plot import DisplayPolarPlot
from karabo.native import Configurable, Hash, Node, VectorDouble
from karabogui.conftest import gui_app
from karabogui.testing import get_class_property_proxy, set_proxy_hash


class PolarizationNode(Configurable):
    theta = VectorDouble()
    radius = VectorDouble()


class TestDevice(Configurable):
    polarization = Node(PolarizationNode)


def test_polar_plot(gui_app: gui_app):
    schema = TestDevice.getClassSchema()
    proxy = get_class_property_proxy(schema, "polarization")
    controller = DisplayPolarPlot(proxy=proxy)
    controller.create(None)

    num_points = 10
    theta = np.arange(num_points)
    radius = np.random.random(num_points)

    set_proxy_hash(proxy, Hash('polarization', Hash("theta", theta)))
    # radius is missing no changes.
    assert len(controller._scatter_plot.points()) == 0
    set_proxy_hash(proxy, Hash("polarization", Hash("theta", theta,
                                                    "radius", radius)))
    assert len(controller._scatter_plot.points()) == num_points
    positions = [[r * np.cos(np.deg2rad(t)), r * np.sin(np.deg2rad(t))]
                 for t, r in zip(theta, radius)]
    for idx, point in enumerate(controller._scatter_plot.points()):
        assert [point.pos().x(), point.pos().y()] == positions[idx]

    num_points = 15
    theta = np.arange(num_points)
    radius = np.random.random(num_points)
    set_proxy_hash(proxy, Hash("polarization", Hash("theta", theta,
                                                    "radius", radius)))
    # length of data has been changed
    assert len(controller._scatter_plot.points()) == num_points
