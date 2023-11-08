import numpy as np
from qtpy.QtCore import Qt

from karabo.native import (
    AccessMode, Configurable, Hash, NDArray, Node, UInt16, VectorUInt16)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

from ..display_detector_cells import (
    BRUSH_DARK, BRUSH_LIT, BRUSH_UNUSED, PEN_UNUSED, RED,
    MultipleDetectorCells, SingleDetectorCells)
from ..utils import get_ndarray_hash_from_data


class OldDetectorCells(Configurable):
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


MAX_NUM_PATTERNS = 10
MAX_NUM_FRAMES = 352


class NewDetectorCells(Configurable):
    displayType = "WidgetNode|MultipleDetectorCells"

    numberOfPatterns = UInt16(
        displayedName="Number of patterns",
        accessMode=AccessMode.READONLY
    )
    nPulsePerFrame = NDArray(
        displayedName="Number of exposed pulses",
        dtype=UInt16,
        shape=(MAX_NUM_PATTERNS, MAX_NUM_FRAMES)
    )


class Object(Configurable):
    oldNode = Node(OldDetectorCells)
    newNode = Node(NewDetectorCells)


class BaseTestCase:

    class DetectorCellsWidget(GuiTestCase):

        node = ''
        controller_klass = None

        def setUp(self):
            super().setUp()
            schema = Object.getClassSchema()
            self.proxy = get_class_property_proxy(schema, self.node)
            self.controller = self.controller_klass(proxy=self.proxy)
            self.controller.create(None)

        def tearDown(self):
            self.controller.destroy()
            assert self.widget is None

        def set_sample_data(self):
            """Set and returns example data to the device
            :returns
            nframe: uint16
            npulse_per_frame: vector of uint16
            """
            raise NotImplementedError("Implemented in subclass")

        def set_values(self, **values):
            hsh = Hash({f'{self.node}.{prop}': value
                        for prop, value in values.items()})
            set_proxy_hash(self.proxy, hsh)

        def test_values(self):
            nfrm, npulse_per_frame = self.set_sample_data()

            self.assertEqual(self.widget.nfrm, nfrm)
            np.testing.assert_array_equal(
                self.widget.npulse_per_frame, npulse_per_frame)

        def test_colors(self):
            cell = self.widget.cells[0]
            self.assertEqual(cell.pen(), PEN_UNUSED)
            self.assertEqual(cell.brush(), BRUSH_UNUSED)

            self.set_sample_data()

            cell = self.widget.cells[0]
            self.assertEqual(cell.pen(), PEN_UNUSED)
            self.assertEqual(cell.brush(), BRUSH_DARK)

            cell = self.widget.cells[1]
            self.assertEqual(cell.pen(), PEN_UNUSED)
            self.assertEqual(cell.brush(), BRUSH_LIT)

        def test_labels(self):
            nlit_label = self.widget.nlit_legend
            ncell_label = self.widget.ncell_legend
            self.assertEqual(nlit_label.toPlainText(), "LIT:    0")
            self.assertEqual(ncell_label.toPlainText(), "USED:   0")

            self.set_sample_data()

            self.assertEqual(nlit_label.toPlainText(), "LIT:    4")
            self.assertEqual(ncell_label.toPlainText(), "USED: 202")

        def test_shape_without_values(self):
            rows, cols = self.model.rows, self.model.columns
            self.assertEqual(self.widget.nrow, rows)
            self.assertEqual(self.widget.ncol, cols)
            self.assertEqual(len(self.widget.cells), rows * cols)

            rows, cols = 40, 20
            self.widget.set_cells(rows, cols)
            self.assertEqual(self.widget.nrow, rows)
            self.assertEqual(self.widget.ncol, cols)
            self.assertEqual(len(self.widget.cells), rows * cols)

        def test_shape_with_values(self):
            self.assertEqual(self.widget.cells[0].brush(), BRUSH_UNUSED)

            self.set_sample_data()
            self.widget.set_cells(40, 20)

            self.assertEqual(self.widget.cells[0].brush(), BRUSH_DARK)
            self.assertEqual(self.widget.cells[1].brush(), BRUSH_LIT)

        def test_background(self):
            view = self.widget.view
            self.assertEqual(view.backgroundBrush().color(), Qt.white)

            # Set the data. The default size should be larger
            self.set_sample_data()
            self.assertEqual(view.backgroundBrush().color(), Qt.white)

            # Set a smaller shape than the actual cells
            self.widget.set_cells(1, 3)
            self.assertEqual(view.backgroundBrush().color(), RED)

        @property
        def model(self):
            return self.controller.model

        @property
        def widget(self):
            return self.controller.widget


class TestOldDetectorCells(BaseTestCase.DetectorCellsWidget):

    node = 'oldNode'
    controller_klass = SingleDetectorCells

    def set_sample_data(self):
        nfrm = 202
        npulse_per_frame = np.zeros(nfrm, dtype=np.uint16)
        npulse_per_frame[1:17:4] = 1
        self.set_values(nFrame=nfrm, nPulsePerFrame=npulse_per_frame)

        return nfrm, npulse_per_frame


class TestNewDetectorCells(BaseTestCase.DetectorCellsWidget):

    node = 'newNode'
    controller_klass = MultipleDetectorCells

    def set_sample_data(self):
        num_pattern = 5
        nfrm = 202
        npulse_per_frame = np.zeros((num_pattern, nfrm), dtype=np.uint16)
        npulse_per_frame[:, 1:17:4] = 1

        ndarray_hsh = get_ndarray_hash_from_data(npulse_per_frame)
        self.set_values(numberOfPatterns=num_pattern,
                        nPulsePerFrame=ndarray_hsh)

        return nfrm, npulse_per_frame[self.controller._index]
