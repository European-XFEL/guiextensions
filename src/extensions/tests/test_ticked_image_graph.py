import numpy as np
import pytest

from karabo.native import (
    Configurable, EncodingType, Hash, Image, ImageData, VectorFloat)
from karabogui.api import PropertyProxy, build_binding
from karabogui.binding.api import DeviceProxy
from karabogui.conftest import gui_app
from karabogui.controllers.display.tests.image import TYPENUM_MAP
from karabogui.testing import set_proxy_hash, set_proxy_value

from ..display_ticked_image_graph import DisplayTickedImageGraph, Transform


class DeviceNode(Configurable):
    x = VectorFloat()
    y = VectorFloat()

    image = Image(data=ImageData(np.zeros((500, 500), dtype=np.float64),
                                 encoding=EncodingType.GRAY),)


@pytest.fixture
def root_proxy():
    binding = build_binding(DeviceNode.getClassSchema())
    return DeviceProxy(binding=binding, device_id="TestDeviceId")


@pytest.fixture
def image_proxy(root_proxy):
    return PropertyProxy(root_proxy=root_proxy, path="image")


@pytest.fixture
def x_proxy(root_proxy):
    return PropertyProxy(root_proxy=root_proxy, path="x")


@pytest.fixture
def y_proxy(root_proxy):
    return PropertyProxy(root_proxy=root_proxy, path="y")


@pytest.fixture
def controller(gui_app: gui_app, image_proxy):
    _controller = DisplayTickedImageGraph(proxy=image_proxy)
    _controller.create(None)
    return _controller


def test_controller_basics(controller, image_proxy):
    # Check proxies: default is None
    assert controller._x_proxy is None
    assert controller._y_proxy is None

    # Check transforms: default is scale=1, offset=0
    assert controller._x_transform == Transform(scale=1, offset=0)
    assert controller._y_transform == Transform(scale=1, offset=0)

    # Check image update
    set_proxy_hash(image_proxy, get_image_hash(dimX=300, dimY=400))
    assert controller._plot.image.shape == (400, 300)


@pytest.mark.parametrize("dims", [(300, 400)])
@pytest.mark.parametrize("x_transform", [(2, 100)])
def test_controller_x_axis(controller, image_proxy, x_proxy,
                           dims, x_transform):
    # Setup
    set_proxy_hash(image_proxy, get_image_hash(dimX=dims[0], dimY=dims[1]))

    # Add and check x-axis proxy
    controller.visualize_additional_property(x_proxy)
    assert controller._x_proxy is x_proxy
    assert controller._y_proxy is None

    # Set and check x-axis transform
    scale, offset = x_transform
    array = np.arange(dims[0]) * scale + offset
    set_proxy_value(x_proxy, 'x', array)
    assert controller._x_transform == Transform(scale=scale, offset=offset)
    assert controller._y_transform == Transform(scale=1, offset=0)

    # Set and check empty array
    set_proxy_value(x_proxy, 'x', [])
    assert controller._x_transform == Transform(scale=1, offset=0)
    assert controller._y_transform == Transform(scale=1, offset=0)


@pytest.mark.parametrize("dims", [(300, 400)])
@pytest.mark.parametrize("x_transform", [(2, 100)])
@pytest.mark.parametrize("y_transform", [(5, 50)])
def test_controller_y_axis(controller, image_proxy, x_proxy, y_proxy,
                           dims, x_transform, y_transform):
    # Setup
    set_proxy_hash(image_proxy, get_image_hash(dimX=dims[0], dimY=dims[1]))

    # Add and check x/y-axes proxies
    controller.visualize_additional_property(x_proxy)
    controller.visualize_additional_property(y_proxy)
    assert controller._x_proxy is x_proxy
    assert controller._y_proxy is y_proxy

    # Set and check x-axis transform
    x_scale, x_offset = x_transform
    array = np.arange(dims[0]) * x_scale + x_offset
    set_proxy_value(x_proxy, 'x', array)
    assert controller._x_transform == Transform(scale=x_scale, offset=x_offset)
    assert controller._y_transform == Transform(scale=1, offset=0)

    # Set and check y-axis transform
    y_scale, y_offset = y_transform
    array = np.arange(dims[1]) * y_scale + y_offset
    set_proxy_value(y_proxy, 'y', array)
    assert controller._x_transform == Transform(scale=x_scale, offset=x_offset)
    assert controller._y_transform == Transform(scale=y_scale, offset=y_offset)

    # Set and check empty array
    set_proxy_value(x_proxy, 'x', [])
    assert controller._x_transform == Transform(scale=1, offset=0)
    assert controller._y_transform == Transform(scale=y_scale, offset=y_offset)

    set_proxy_value(y_proxy, 'y', [])
    assert controller._x_transform == Transform(scale=1, offset=0)
    assert controller._y_transform == Transform(scale=1, offset=0)


def _get_geometry_hash(update):
    alignment_hash = Hash('offsets', [0., 0., 0.],
                          'rotations', [0., 0., 0.])
    return Hash('update', update,
                'pixelRegion', [0, 0, 1, 1],  # x0, y0, x1, y1
                'alignment', alignment_hash)


def get_image_hash(val=0, dimZ=None, *, dimX, dimY,
                   encoding=EncodingType.GRAY, update=True):
    npix = dimX * dimY
    dims_val = [dimY, dimX]
    if dimZ:
        dims_val.append(dimZ)
        npix *= dimZ
    pixel_hsh = Hash('type', TYPENUM_MAP['uint8'],
                     'data', bytearray([val for _ in range(npix)]))
    img_hsh = Hash('pixels', pixel_hsh,
                   'dims', dims_val,
                   'geometry', _get_geometry_hash(update),
                   'encoding', encoding)
    return Hash('image', img_hsh)
