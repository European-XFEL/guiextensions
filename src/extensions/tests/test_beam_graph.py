import numpy as np

from extensions.display_beam_graph import BeamGraph
from extensions.utils import reflect_angle
from karabo.native import (
    Configurable, Double, EncodingType, Hash, Image, ImageData, Node)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)


# Output channel
class DataNode(Configurable):
    image = Image(data=ImageData(np.zeros((500, 500), dtype=np.float64),
                                 encoding=EncodingType.GRAY),
                  displayedName="Image")


class ChannelNode(Configurable):
    data = Node(DataNode)


# Beam nodes
class PropertiesNode(Configurable):
    energy = Double()

    x0 = Double()
    y0 = Double()

    a = Double()
    b = Double()

    theta = Double()
    peak = Double()


class ObjectNode(Configurable):
    prop = Node(PropertiesNode)


class TestBeamGraph(GuiTestCase):
    def setUp(self):
        super(TestBeamGraph, self).setUp()
        output_schema = ChannelNode.getClassSchema()
        self.image_proxy = get_class_property_proxy(output_schema, 'data')
        device_schema = ObjectNode.getClassSchema()
        self.ellipse_proxy = get_class_property_proxy(device_schema, 'prop')
        self.controller = BeamGraph(proxy=self.image_proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.widget is None

    def test_basics(self):
        image_node = self.controller._image_node
        self.assertFalse(image_node.is_valid)

        ellipse = self.controller._ellipse
        self.assertIsNone(ellipse)

    def test_ellipse_basics(self):
        # Add proxy
        self.controller.visualize_additional_property(self.ellipse_proxy)

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
        # Add proxy
        self.controller.visualize_additional_property(self.ellipse_proxy)
        # Update proxy
        beam = {"x0": 200, "y0": 150,
                "a": 20, "b": 20,
                "theta": 30}
        self.update_proxy(self.ellipse_proxy, **beam)

        angle = reflect_angle(beam["theta"])
        ellipse = self.controller._ellipse
        self.assertEqual(ellipse.position, (beam["x0"], beam["y0"]))
        self.assertEqual(ellipse.size, (beam["a"], beam["b"]))
        self.assertEqual(ellipse.angle, angle)
        self.assertTrue(ellipse.is_visible)

        x0, y0 = ellipse._calc_position(center=(beam["x0"], beam["y0"]),
                                        axes=(beam["a"], beam["b"]),
                                        angle=np.deg2rad(angle))
        self.assertEqual(ellipse._item_position, (x0, y0))
        self.assertEqual(ellipse._item_size, (beam["a"], beam["b"]))
        self.assertEqual(ellipse.roi_item.angle(), angle)
        self.assertTrue(ellipse.roi_item.isVisible())

        crosshair = ellipse.crosshair_item
        pos = crosshair.pos()
        self.assertEqual((pos[0], pos[1]), (beam["x0"], beam["y0"]))
        size = crosshair.size()
        self.assertEqual((size[0], size[1]), (beam["a"], beam["b"]))
        self.assertEqual(crosshair.angle(), angle)
        self.assertTrue(crosshair.isVisible())

    def test_invalid_beam(self):
        # Add proxy
        self.controller.visualize_additional_property(self.ellipse_proxy)
        # Update proxy
        beam = {"x0": np.nan, "y0": np.nan,
                "a": np.nan, "b": np.nan,
                "theta": np.nan}
        self.update_proxy(self.ellipse_proxy, **beam)

        angle = reflect_angle(0)
        ellipse = self.controller._ellipse
        self.assertEqual(ellipse.position, (0, 0))
        self.assertEqual(ellipse.size, (0, 0))
        self.assertEqual(ellipse.angle, angle)
        self.assertFalse(ellipse.is_visible)

        self.assertEqual(ellipse._item_position, (0, 0))
        self.assertEqual(ellipse._item_size, (0, 0))
        self.assertEqual(ellipse.roi_item.angle(), angle)
        self.assertFalse(ellipse.roi_item.isVisible())

        crosshair = ellipse.crosshair_item
        pos = crosshair.pos()
        self.assertEqual((pos[0], pos[1]), (0, 0))
        size = crosshair.size()
        self.assertEqual((size[0], size[1]), (0, 0))
        self.assertEqual(crosshair.angle(), angle)
        self.assertFalse(crosshair.isVisible())

    # ---------------------------------------------------------------------
    # Helpers

    def update_proxy(self, proxy, **kwargs):
        corrected = {f"{proxy.path}.{key}": value
                     for key, value in kwargs.items()}
        set_proxy_hash(proxy, Hash(corrected))

    @property
    def widget(self):
        return self.controller.widget
