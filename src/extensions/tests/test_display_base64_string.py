from base64 import b64encode
from pathlib import Path

import pytest
from qtpy.QtGui import QPixmap

from extensions.display_base64_string import DisplayBase64Image
from karabo.native import Configurable, String
from karabogui import icons
from karabogui.testing import get_class_property_proxy, set_proxy_value

PIXELS = 1024
IMAGE_SIZE = PIXELS, PIXELS


class Logger(Configurable):
    base64String = String()


def get_image(icon):
    path = Path(icons.__file__).parent / icon
    with open(path, "rb") as image:
        image_byte = image.read()
    b64contents = b64encode(image_byte)
    image_string = b64contents.decode()
    return image_string, image_byte


@pytest.fixture()
def controller_widget(gui_app):
    schema = Logger.getClassSchema()
    proxy = get_class_property_proxy(schema, "base64String")
    controller = DisplayBase64Image(proxy=proxy)
    controller.create(None)
    yield controller

    controller.destroy()
    assert controller.widget is None


def test_set_value(controller_widget):
    proxy = controller_widget.proxy
    image_string, image_bytes = get_image("splash.png")
    set_proxy_value(proxy, "base64String",
                    f"data:image/png;base64,{image_string}")
    pixmap = QPixmap()
    pixmap.loadFromData(image_bytes)
    assert controller_widget.widget.pixmap().toImage() == pixmap.toImage()
