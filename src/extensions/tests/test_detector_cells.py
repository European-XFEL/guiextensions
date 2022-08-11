import numpy as np

from karabo.native import (
    AccessMode, Configurable, Hash, Node, UInt16, VectorUInt16)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

from ..display_detector_cells import (
    BRUSH_DARK, BRUSH_LIT, BRUSH_UNUSED, PEN_UNUSED, DetectorCells)


class DetectorCellsNode(Configurable):
    displayType = "WidgetNode|DetectorCells"

    nFrame = UInt16(
        displayedName="Number of Frames",
        accessMode=AccessMode.READONLY
    )
    nPulsePerFrame = VectorUInt16(
        displayedName="Number of exposed pulses",
        maxSize=352,
        accessMode=AccessMode.READONLY
    )


class Object(Configurable):
    node = Node(DetectorCellsNode)


class TestDetectorCellsWidget(GuiTestCase):
    def setUp(self):
        super().setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = DetectorCells(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):
        nfrm = 202
        npulse_per_frame = np.zeros(nfrm, dtype=np.uint16)
        npulse_per_frame[1:17:4] = 1

        set_proxy_hash(self.proxy, Hash(
            'node.nFrame', nfrm,
            'node.nPulsePerFrame', npulse_per_frame,
        ))
        self.assertEqual(self.controller.widget.nfrm, nfrm)
        np.testing.assert_array_equal(
            self.controller.widget.npulse_per_frame, npulse_per_frame)

    def test_colors(self):
        cell = self.controller.widget.cells[0]
        self.assertEqual(cell.pen(), PEN_UNUSED)
        self.assertEqual(cell.brush(), BRUSH_UNUSED)

        nfrm = 202
        npulse_per_frame = np.zeros(nfrm, dtype=np.uint16)
        npulse_per_frame[1:15:4] = 1

        set_proxy_hash(self.proxy, Hash(
            'node.nFrame', nfrm,
            'node.nPulsePerFrame', npulse_per_frame,
        ))

        cell = self.controller.widget.cells[0]
        self.assertEqual(cell.pen(), PEN_UNUSED)
        self.assertEqual(cell.brush(), BRUSH_DARK)

        cell = self.controller.widget.cells[1]
        self.assertEqual(cell.pen(), PEN_UNUSED)
        self.assertEqual(cell.brush(), BRUSH_LIT)

    def test_labels(self):
        nlit_label = self.controller.widget.nlit_legend
        ncell_label = self.controller.widget.ncell_legend
        self.assertEqual(nlit_label.toPlainText(), "LIT:   0")
        self.assertEqual(ncell_label.toPlainText(), "USED:   0")

        nfrm = 202
        npulse_per_frame = np.zeros(nfrm, dtype=np.uint16)
        npulse_per_frame[1:15:4] = 1

        set_proxy_hash(self.proxy, Hash(
            'node.nFrame', nfrm,
            'node.nPulsePerFrame', npulse_per_frame,
        ))

        self.assertEqual(nlit_label.toPlainText(), "LIT:   4")
        self.assertEqual(ncell_label.toPlainText(), "USED: 202")
