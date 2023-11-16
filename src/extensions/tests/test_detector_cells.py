import numpy as np
from qtpy.QtCore import Qt

from karabo.common.api import State
from karabo.native import (
    AccessMode, Configurable, Hash, NDArray, Node, String, UInt16,
    VectorUInt16)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

from ..display_detector_cells import (
    RED, CellStyle, MultipleDetectorCells, SingleDetectorCells)
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
    shutterState = String(
        defaultValue=State.OPENED,
        enum=State,
        displayType='State')


class BaseTestCase:

    class DetectorCellsWidget(GuiTestCase):

        node = ''
        controller_klass = None

        def setUp(self):
            super().setUp()
            schema = Object.getClassSchema()
            self.cells_proxy = get_class_property_proxy(schema, self.node)
            self.controller = self.controller_klass(proxy=self.cells_proxy)
            self.controller.create(None)

            # Add proxy
            self.state_proxy = get_class_property_proxy(schema, 'shutterState')
            self.controller.visualize_additional_property(self.state_proxy)

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
            set_proxy_hash(self.cells_proxy, hsh)

        def test_values(self):
            nfrm, npulse_per_frame = self.set_sample_data()

            self.assertEqual(self.widget.nfrm, nfrm)
            np.testing.assert_array_equal(
                self.widget.cell_style_codes, npulse_per_frame + 1)

        def test_colors(self):
            cell = self.widget.cells[0]
            self.assertEqual(cell.pen(), CellStyle.UNUSED.pen)
            self.assertEqual(cell.brush(), CellStyle.UNUSED.brush)

            self.set_sample_data()

            cell = self.widget.cells[0]
            self.assertEqual(cell.pen(), CellStyle.DARK.pen)
            self.assertEqual(cell.brush(), CellStyle.DARK.brush)

            cell = self.widget.cells[1]
            self.assertEqual(cell.pen(), CellStyle.LIT.pen)
            self.assertEqual(cell.brush(), CellStyle.LIT.brush)

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
            self.assertEqual(self.widget.cells[0].brush(),
                             CellStyle.UNUSED.brush)

            self.set_sample_data()
            self.widget.set_cells(40, 20)

            self.assertEqual(self.widget.cells[0].brush(),
                             CellStyle.DARK.brush)
            self.assertEqual(self.widget.cells[1].brush(),
                             CellStyle.LIT.brush)

        def test_background(self):
            view = self.widget.view
            self.assertEqual(view.backgroundBrush().color(), Qt.white)

            # Set the data. The default size should be larger
            self.set_sample_data()
            self.assertEqual(view.backgroundBrush().color(), Qt.white)

            # Set a smaller shape than the actual cells
            self.widget.set_cells(1, 3)
            self.assertEqual(view.backgroundBrush().color(), RED)

        def test_state_proxy(self):
            self.set_sample_data()

            # Test the open state
            set_proxy_hash(self.state_proxy, Hash('shutterState', 'OPEN'))

            cell = self.widget.cells[0]
            self.assertEqual(cell.pen(), CellStyle.DARK.pen)
            self.assertEqual(cell.brush(), CellStyle.DARK.brush)

            cell = self.widget.cells[1]
            self.assertEqual(cell.pen(), CellStyle.LIT.pen)
            self.assertEqual(cell.brush(), CellStyle.LIT.brush)

            cell = self.widget.cells[202]
            self.assertEqual(cell.pen(), CellStyle.UNUSED.pen)
            self.assertEqual(cell.brush(), CellStyle.UNUSED.brush)

            # Test the closed state
            set_proxy_hash(self.state_proxy, Hash('shutterState', 'CLOSED'))

            cell = self.widget.cells[0]
            self.assertEqual(cell.pen(), CellStyle.DARK.pen)
            self.assertEqual(cell.brush(), CellStyle.DARK.brush)

            cell = self.widget.cells[1]
            self.assertEqual(cell.pen(), CellStyle.LIT_BLOCKED.pen)
            self.assertEqual(cell.brush(), CellStyle.LIT_BLOCKED.brush)

            cell = self.widget.cells[202]
            self.assertEqual(cell.pen(), CellStyle.UNUSED.pen)
            self.assertEqual(cell.brush(), CellStyle.UNUSED.brush)

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
