import numpy as np
from PyQt5.QtGui import QBrush, QPen

from karabo.middlelayer import AccessMode, Configurable, Hash, Node, VectorBool
from karabogui.testing import (
    get_class_property_proxy, GuiTestCase, set_proxy_hash
)

from ..pulse_info import (
    BRUSH_EMPTY, BRUSH_FEL, PEN_EMPTY, PEN_DET, PulseIdMap
)


class PINode(Configurable):
    displayType = "WidgetNode|PulseId-Map"

    fel = VectorBool(displayedName="FEL Pulses",
                     accessMode=AccessMode.READONLY,
                     defaultValue=[])

    ppl = VectorBool(displayedName="PPL Pulses",
                     accessMode=AccessMode.READONLY,
                     defaultValue=[])

    det = VectorBool(displayedName="Detector Pulses",
                     accessMode=AccessMode.READONLY,
                     defaultValue=[])


class Object(Configurable):
    node = Node(PINode)


class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = PulseIdMap(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):
        fel = np.random.randint(0, 1, size=(2700,), dtype=np.bool_)
        ppl = np.random.randint(0, 1, size=(2700,), dtype=np.bool_)
        det = np.random.randint(0, 1, size=(2700,), dtype=np.bool_)

        set_proxy_hash(
            self.proxy,
            Hash('node.fel', fel,
                 'node.ppl', ppl,
                 'node.det', det)
        )
        self.assertEqual(self.controller.widget.fel, fel)
        self.assertEqual(self.controller.widget.ppl, ppl)
        self.assertEqual(self.controller.widget.det, det)

    def test_colors(self):
        fel, ppl = self.controller.widget.pulses[0]
        self.assertEqual(fel.pen(), PEN_EMPTY)
        self.assertEqual(fel.brush(), BRUSH_EMPTY)
        self.assertEqual(ppl.visible(), False)

        self.proxy.value.fel.value = np.ones(2700, dtype=np.bool_)
        self.proxy.value.ppl.value = np.ones(2700, dtype=np.bool_)
        self.proxy.value.det.value = np.ones(2700, dtype=np.bool_)

        self.controller.value_update(self.proxy)

        fel, ppl = self.controller.widget.pulses[0]
        self.assertEqual(fel.pen(), PEN_DET)
        self.assertEqual(fel.brush(), BRUSH_FEL)
        self.assertEqual(ppl.isVisible(), True)
