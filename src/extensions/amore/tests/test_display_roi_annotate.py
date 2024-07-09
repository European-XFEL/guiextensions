import pytest

from extensions.amore.display_roi_annotate import DisplayImageAnnotate
from karabo.native import Configurable, Float, Int32, Node, String
from karabogui.testing import get_class_property_proxy

PIXELS = 1024
IMAGE_SIZE = PIXELS, PIXELS


class Coordinates(Configurable):
    annotation = String()
    horizontal = Float()
    horizontalSize = Float()
    vertical = Float()
    verticalSize = Float()
    roiTool = Int32()
    date = String()


class Logger(Configurable):
    hisotoricAnnotation = Node(Coordinates)


@pytest.fixture
def controller_widget(gui_app):
    schema = Logger.getClassSchema()
    proxy = get_class_property_proxy(schema, "historicAnnotation")
    controller = DisplayImageAnnotate(proxy=proxy)
    controller.create(None)
    yield controller

    controller.destroy()
    assert controller.widget is None


def test_annotate_display(controller_widget):
    """Test that default annotation type is 2"""
    assert controller_widget.annotation_type == 2
