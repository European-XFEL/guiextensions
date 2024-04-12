from base64 import b64encode
from pathlib import Path

import pytest
from qtpy.QtCore import QPoint, QRectF, Qt
from qtpy.QtGui import QPixmap
from qtpy.QtTest import QTest

from extensions.display_base64_string import DisplayBase64Image, MouseMode
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


def define_zoom_region(zoom_factor):
    # Calculate expected zoomed region
    initial_zoomed_region = QRectF(0.0, 0.0, 100.0, 100.0)
    top_left_point = initial_zoomed_region.topLeft()
    expected_scene_zoomed_region = QRectF(
        (top_left_point.x() + (1 - zoom_factor) /
         2 * initial_zoomed_region.width()),
        (top_left_point.y() + (1 - zoom_factor) /
         2 * initial_zoomed_region.height()),
        (initial_zoomed_region.width() * zoom_factor),
        (initial_zoomed_region.height() * zoom_factor))
    return expected_scene_zoomed_region


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
    controller_widget.widget.view.pixmap_item.setPixmap(pixmap)
    pixmap_image = (
        controller_widget.widget.view.pixmap_item.pixmap().toImage())
    assert (pixmap_image == pixmap.toImage())


def test_on_mouse_zoom(controller_widget):
    """Test the on_mouse_move method."""

    controller_widget.widget.zoom_in_action.trigger()
    assert controller_widget.widget.mouse_mode == MouseMode.Zoom
    assert controller_widget.widget.zoom_in_action.isChecked()


def test_on_mouse_move(controller_widget):
    """Test the on_mouse_move method."""

    controller_widget.widget.move_action.trigger()
    assert controller_widget.widget.mouse_mode == MouseMode.Move
    assert controller_widget.widget.move_action.isChecked()


def test_on_mouse_pointer(controller_widget):
    """Test the on_mouse_move method."""

    controller_widget.widget.pointer_action.trigger()
    assert controller_widget.widget.mouse_mode == MouseMode.Pointer
    assert controller_widget.widget.pointer_action.isChecked()


def test_move_mode_pointer(controller_widget):
    """
    Test the pointer mode in move mode.

    This test triggers the pointer mode, calculates the expected zoomed region,
    calls the method to zoom in, and verifies that the scene zoomed region is
    updated accordingly.

    Args:
    - controller_widget: An instance of the controller widget containing the
      widget to be tested.
    """

    # Trigger the pointer mode
    controller_widget.widget.pointer_action.trigger()

    # Calculate expected zoomed region
    zoom_factor = 1.5
    expected_scene_zoomed_region = define_zoom_region(zoom_factor)

    # Call the method to zoom in
    controller_widget.widget.view.scene.setSceneRect(
        expected_scene_zoomed_region)

    # Verify that the scene zoomed region is updated accordingly
    assert controller_widget.widget.view.scene.sceneRect() == \
        expected_scene_zoomed_region


def test_zoom_to_maximum(controller_widget):
    """
    Test the zoom functionality of the widget by simulating the process of
    zooming in to the maximum level.

    This test triggers the pointer mode, simulates a mouse press and release
    event to initiate the zoom action, calculates the expected zoomed region
    based on the zoom factor, and verifies that the scene zoomed region is
    updated accordingly.

    Args:
    - controller_widget: An instance of the controller widget containing the
      widget to be tested.
    """

    # Trigger pointer mode
    controller_widget.widget.pointer_action.trigger()

    # Calculate expected zoomed region
    zoom_factor = 1.5
    expected_scene_zoomed_region = define_zoom_region(zoom_factor)
    initial_zoomed_region = QRectF(0.0, 0.0, 100.0, 100.0)
    pixmap = QPixmap(initial_zoomed_region.size().toSize())
    controller_widget.widget.view.pixmap_item.setPixmap(pixmap)

    # Call the method to zoom in
    controller_widget.widget.view.scene.setSceneRect(
        expected_scene_zoomed_region)

    # Verify that the scene zoomed region is updated accordingly
    assert controller_widget.widget.view.scene.sceneRect() == \
        expected_scene_zoomed_region

    # Simulate mouse press and release event to initiate the zoom action
    QTest.mouseRelease(controller_widget.widget.view.viewport(),
                       Qt.RightButton, Qt.NoModifier, QPoint(100, 100))
    assert controller_widget.widget.view.scene.sceneRect() != \
        expected_scene_zoomed_region

    # Trigger pointer mode
    controller_widget.widget.pointer_action.trigger()

    # Calculate expected zoomed region
    zoom_factor = 1
    expected_scene_zoomed_region = define_zoom_region(zoom_factor)

    # Call the method to zoom in
    controller_widget.widget.view.scene.setSceneRect(
        expected_scene_zoomed_region)

    # Simulate mouse press and release event to initiate the zoom action
    QTest.mouseRelease(controller_widget.widget.view.viewport(),
                       Qt.RightButton, Qt.NoModifier, QPoint(50, 50))
    assert controller_widget.widget.view.scene.sceneRect() == \
        expected_scene_zoomed_region
