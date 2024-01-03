import numpy as np

from extensions.display_beam_graph import BeamGraph
from extensions.utils import reflect_angle
from karabo.native import (
    Configurable, Double, EncodingType, Hash, Image, ImageData, Node, String,
    VectorDouble)
from karabogui.controllers.display.tests.image import get_image_hash
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


class PropertiesNode(Configurable):
    energy = Double()
    x0 = Double()
    y0 = Double()
    a = Double()
    b = Double()
    theta = Double()
    peak = Double()
    lastUpdated = String()


class TransformNode(Configurable):
    pixelScale = Double()
    pixelTranslate = VectorDouble()


# Output channel
class DataNode(Configurable):
    image = Image(data=ImageData(np.zeros((500, 500), dtype=np.float64),
                                 encoding=EncodingType.GRAY),
                  displayedName="Image")
    beamProperties = Node(PropertiesNode)
    transform = Node(TransformNode)


class ChannelNode(Configurable):
    data = Node(DataNode)


class TestBeamGraph(GuiTestCase):
    def setUp(self):
        super(TestBeamGraph, self).setUp()
        output_schema = ChannelNode.getClassSchema()
        self.beam_proxy = get_class_property_proxy(output_schema, 'data')
        self.controller = BeamGraph(proxy=self.beam_proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_basics(self):
        image_node = self.controller._image_node
        self.assertFalse(image_node.is_valid)

        ellipse = self.controller._ellipse
        self.assertIsNotNone(ellipse)

    def test_ellipse_basics(self):
        ellipse = self.controller._ellipse
        self.assertIsNotNone(ellipse)

        self.assertEqual(ellipse.position, (0, 0))
        self.assertEqual(ellipse.size, (0, 0))
        self.assertEqual(ellipse.angle, 0)
        self.assertFalse(ellipse.is_visible)

        self.assertEqual(ellipse._item_position, (0, 0))
        self.assertEqual(ellipse._item_size, (0, 0))
        self.assertEqual(ellipse.roi_item.angle(), 0)
        self.assertFalse(ellipse.roi_item.isVisible())

        crosshair = ellipse.crosshair_item
        pos = crosshair.pos()
        self.assertEqual((pos[0], pos[1]), (0, 0))
        size = crosshair.size()
        self.assertEqual((size[0], size[1]), (0, 0))
        self.assertEqual(crosshair.angle(), 0)
        self.assertFalse(crosshair.isVisible())

    def test_normal_beam(self):
        # Update proxy
        beam = {"x0": 200, "y0": 150,
                "a": 20, "b": 20,
                "theta": 30}
        self.update_proxy(beamProperties=beam)

        ellipse = self.controller._ellipse
        self.assertEqual(ellipse.position, (beam["x0"], beam["y0"]))
        self.assertEqual(ellipse.size, (beam["a"], beam["b"]))
        self.assertEqual(ellipse.angle, beam["theta"])
        self.assertTrue(ellipse.is_visible)

        reflected = reflect_angle(beam["theta"])
        x0, y0 = ellipse._calc_position(center=(beam["x0"], beam["y0"]),
                                        widths=(beam["a"], beam["b"]),
                                        angle=np.deg2rad(reflected))
        self.assertEqual(ellipse._item_position, (x0, y0))
        self.assertEqual(ellipse._item_size, (beam["a"], beam["b"]))
        self.assertEqual(ellipse.roi_item.angle(), reflected)
        self.assertTrue(ellipse.roi_item.isVisible())

        crosshair = ellipse.crosshair_item
        pos = crosshair.pos()
        self.assertEqual((pos[0], pos[1]), (beam["x0"], beam["y0"]))
        size = crosshair.size()
        self.assertEqual((size[0], size[1]), (beam["a"], beam["b"]))
        self.assertEqual(crosshair.angle(), reflected)
        self.assertTrue(crosshair.isVisible())

    def test_invalid_beam(self):
        # Update proxy
        beam = {"x0": np.nan, "y0": np.nan,
                "a": np.nan, "b": np.nan,
                "theta": np.nan}
        self.update_proxy(beamProperties=beam)

        ellipse = self.controller._ellipse
        self.assertEqual(ellipse.position, (0, 0))
        self.assertEqual(ellipse.size, (0, 0))
        self.assertEqual(ellipse.angle, 0)
        self.assertFalse(ellipse.is_visible)

        self.assertEqual(ellipse._item_position, (0, 0))
        self.assertEqual(ellipse._item_size, (0, 0))
        self.assertEqual(ellipse.roi_item.angle(), 180)  # reflected
        self.assertFalse(ellipse.roi_item.isVisible())

        crosshair = ellipse.crosshair_item
        pos = crosshair.pos()
        self.assertEqual((pos[0], pos[1]), (0, 0))
        size = crosshair.size()
        self.assertEqual((size[0], size[1]), (0, 0))
        self.assertEqual(crosshair.angle(), 180)  # reflected
        self.assertFalse(crosshair.isVisible())

    # ---------------------------------------------------------------------
    # Helpers

    def update_proxy(self, **kwargs):
        props = {key: Hash(value) for key, value in kwargs.items()}
        hsh = Hash({'transform': {'pixelScale': 1, 'pixelTranslate': 0},
                    **get_image_hash(),
                    **props})

        set_proxy_hash(self.beam_proxy, Hash(self.beam_proxy.path, hsh))

    @property
    def widget(self):
        return self.controller.widget
