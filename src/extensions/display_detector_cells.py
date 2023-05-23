import numpy as np
from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPen
from qtpy.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSpinBox, QWidget)
from traits.api import Bool, Instance, Int

from karabogui.binding.api import WidgetNodeBinding, get_binding_value
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.fonts import get_font_size_from_dpi

from .models.api import DetectorCellsModel, MultipleDetectorCellsModel
from .utils import get_array_data

GRAY = QColor(127, 127, 127, 255)
BLUE = QColor(31, 119, 180, 255)
ORANGE = QColor(255, 127, 14, 255)

BRUSH_UNUSED = QBrush(GRAY)
BRUSH_DARK = QBrush(BLUE)
BRUSH_LIT = QBrush(ORANGE)
PEN_UNUSED = QPen(Qt.transparent)

ALGN_CENTER = 1
ALGN_TOP = 0
ALGN_BOTTOM = 2
ALGN_LEFT = 0
ALGN_RIGHT = 2

CELL_BRUSH = (BRUSH_UNUSED, BRUSH_DARK, BRUSH_LIT)

OFFSET_H = 40
OFFSET_V = 40
GAP_H = 3
GAP_V = 3
SIDE = 12
TICK_LEN = 6
STRIDE_H = SIDE + GAP_H
STRIDE_V = SIDE + GAP_H
STRIDE_LEGEND = 70

NUM_PATTERNS_START = 1
DEFAULT_NUM_PATTERNS = NUM_PATTERNS_START + 0  # no pattern


class DetectorCellsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.nrow = 11
        self.ncol = 32
        self.cells = []

        self.nfrm = 0
        self.npulse_per_frame = np.zeros(self.nfrm, dtype=np.uint16)

        width = OFFSET_H + self.ncol * STRIDE_H - GAP_H + 10
        height = OFFSET_V + self.nrow * STRIDE_V - GAP_V + 40

        grid = QGridLayout(self)
        self.view = QGraphicsView()
        grid.addWidget(self.view)
        self.view.setRenderHints(QPainter.Antialiasing)

        # Add slider
        self.npattern_slider = slider = QSlider(Qt.Horizontal)
        slider.setSingleStep(1)
        slider.setMinimum(NUM_PATTERNS_START)
        slider.setMaximum(DEFAULT_NUM_PATTERNS)
        slider.setTickInterval(1)
        slider.setTickPosition(QSlider.TicksBelow)

        # Add spinbox
        self.npattern_spinbox = spinbox = QSpinBox()
        spinbox.setMinimumWidth(80)
        spinbox.setMinimum(NUM_PATTERNS_START)
        spinbox.setMaximum(DEFAULT_NUM_PATTERNS)

        # Add label
        self.npattern_label = label = QLabel()

        # Add union button
        self.button = button = QPushButton('Union')
        button.setCheckable(True)
        button.setMinimumWidth(80)

        # Add layout
        pattern_hbox = QHBoxLayout()
        pattern_hbox.addWidget(slider)
        pattern_hbox.addWidget(spinbox)
        pattern_hbox.addWidget(label)

        control_hbox = QHBoxLayout()
        grid.addLayout(control_hbox, 2, 0)
        control_hbox.addWidget(QLabel("Pattern no.:"))
        control_hbox.addLayout(pattern_hbox, stretch=5)
        control_hbox.addStretch(1)
        control_hbox.addWidget(button, stretch=2)

        # Add signals
        slider.valueChanged[int].connect(spinbox.setValue)
        spinbox.valueChanged[int].connect(slider.setValue)
        button.toggled.connect(self._enable_pattern_slice)
        self.set_num_patterns(0)

        self.scene = QGraphicsScene(0, 0, width, height)
        self.view.setScene(self.scene)

        self.draw_cell_matrix()

    def add_text(self, text, x, y, va=ALGN_CENTER, ha=ALGN_CENTER,
                 font='Courier', size=9):
        t = self.scene.addText(text)

        size = get_font_size_from_dpi(size)
        t.setFont(QFont(font, size, QFont.Light))

        brect = t.boundingRect()
        t.setPos(x - ha * brect.width() / 2, y - va * brect.height() / 2)

        return t

    def draw_cell_matrix(self):
        rect = QRectF(0, 0, SIDE, SIDE)

        y = OFFSET_V
        for row in range(self.nrow):
            # add y-tick label
            self.add_text(f'{row * self.ncol}',
                          OFFSET_H, y + SIDE / 2, ha=ALGN_RIGHT)

            x = OFFSET_H
            for col in range(self.ncol):
                # add x-tick labels
                if col % 10 == 0:
                    xpos = x + SIDE / 2
                    ypos = OFFSET_V - GAP_V
                    self.scene.addLine(xpos, ypos, xpos, ypos - TICK_LEN)
                    self.add_text(f'{col}',
                                  xpos, ypos - TICK_LEN, va=ALGN_BOTTOM)

                # background representing fel/no-fel
                cell = self.scene.addRect(
                    rect.translated(x, y), PEN_UNUSED, BRUSH_UNUSED)

                self.cells.append(cell)
                x += STRIDE_H

            y += STRIDE_V

        # add legend
        y += STRIDE_V
        ypos = y + SIDE / 2
        x = OFFSET_H
        self.scene.addRect(rect.translated(x, y), PEN_UNUSED, BRUSH_UNUSED)
        self.add_text('UNUSED', x + SIDE, ypos, ha=ALGN_LEFT)
        x += STRIDE_LEGEND
        self.scene.addRect(rect.translated(x, y), PEN_UNUSED, BRUSH_DARK)
        self.add_text('DARK', x + SIDE, ypos, ha=ALGN_LEFT)
        x += STRIDE_LEGEND
        self.scene.addRect(rect.translated(x, y), PEN_UNUSED, BRUSH_LIT)
        self.add_text('LIT', x + SIDE, ypos, ha=ALGN_LEFT)

        x = OFFSET_H + self.ncol * STRIDE_H - GAP_H
        self.nlit_legend = self.add_text("LIT:   0", x, ypos, ha=ALGN_RIGHT)
        x -= 100
        self.ncell_legend = self.add_text("USED:   0", x, ypos, ha=ALGN_RIGHT)

    def set_parameters(self, nfrm, npulse_per_frame):
        if len(npulse_per_frame) != nfrm:
            npulse_per_frame = np.zeros(nfrm, dtype=np.uint16)

        nsmall = min(nfrm, self.nfrm)
        nlarge = max(nfrm, self.nfrm)
        pulse_diff = np.where(self.npulse_per_frame[:nsmall]
                              != npulse_per_frame[:nsmall])[0]
        used_diff = np.arange(nsmall, nlarge)

        changed_cells = np.unique(np.concatenate([pulse_diff, used_diff]))
        for i in changed_cells:
            cell = self.cells[i]
            cell_state = int(npulse_per_frame[i] > 0) + 1 if i < nfrm else 0
            cell.setBrush(CELL_BRUSH[cell_state])

        self.nfrm = nfrm
        self.npulse_per_frame = npulse_per_frame
        nlit = np.sum(npulse_per_frame > 0)

        self.ncell_legend.setPlainText(f"USED: {nfrm:3d}")
        self.nlit_legend.setPlainText(f"LIT: {nlit:3d}")

        self.update()

    def set_num_patterns(self, value):
        self.npattern_slider.setMinimum(1 if value else 0)
        self.npattern_spinbox.setMinimum(1 if value else 0)

        self.npattern_slider.setMaximum(value)
        self.npattern_spinbox.setMaximum(value)
        self.npattern_label.setText(f'of {value}')

        is_single_pattern = value <= 1
        is_union = self.button.isChecked()
        self.npattern_slider.setDisabled(is_union or is_single_pattern)
        self.npattern_spinbox.setDisabled(is_union or is_single_pattern)
        self.button.setDisabled(is_single_pattern)

    def _enable_pattern_slice(self, enabled):
        is_single_pattern = self.npattern_slider.maximum() <= 1
        self.npattern_slider.setDisabled(enabled or is_single_pattern)
        self.npattern_spinbox.setDisabled(enabled or is_single_pattern)


class BaseDetectorCellsController(BaseBindingController):
    """Base class for the detector cells controller.

    This enables support of the old schema (single pattern)
    and the new schema (multiple pattern) using the same widget."""

    _is_union = Bool(False)
    _index = Int

    def create_widget(self, parent):
        widget = DetectorCellsWidget(parent)
        return widget

    def binding_update(self, proxy):
        self.value_update(proxy)

    def value_update(self, proxy):
        """Reimplemented in subclasses"""


@register_binding_controller(
    ui_name='Detector Cells Widget',
    klassname='DetectorCells',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|DetectorCells'),
    priority=0, can_show_nothing=False)
class SingleDetectorCells(BaseDetectorCellsController):
    """Show a matrix representing the detector memory cells

    This widget is used with a special widget node type: DetectorCells.
    In this node we expect to have two properties:

    :param nFrame: UInt16
    :param nPulsePerFrame: VectorUInt16
    """
    model = Instance(DetectorCellsModel, args=())

    def value_update(self, proxy):
        node = get_binding_value(proxy)
        if node is None:
            return

        nfrm = get_binding_value(node.nFrame, default=0)
        npulse_per_frame = get_binding_value(
            node.nPulsePerFrame, default=np.zeros(nfrm, np.uint16))
        self.widget.set_parameters(nfrm, npulse_per_frame)


@register_binding_controller(
    ui_name='Detector Cells Widget',
    klassname='MultipleDetectorCells',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|MultipleDetectorCells'),
    priority=0, can_show_nothing=False)
class MultipleDetectorCells(BaseDetectorCellsController):
    """Show a matrix representing the detector memory cells

    This widget is used with a special widget node type: MultipleDetectorCells.
    In this node we expect to have two properties:

    :param numberOfPatterns: UInt16
    :param nPulsePerFrame: NDArray, with shape = (nFrame, numberOfPatterns)
    """
    model = Instance(MultipleDetectorCellsModel, args=())

    def create_widget(self, parent):
        widget = super().create_widget(parent)
        widget.npattern_slider.valueChanged[int].connect(self._update_index)
        widget.button.toggled.connect(self._enable_union)
        return widget

    def value_update(self, proxy):
        node = get_binding_value(proxy)
        if node is None:
            return

        # 0. Get values
        npulse_per_frame, _ = get_array_data(
            node.nPulsePerFrame, default=np.array([[]], dtype=np.uint16))

        # 1. Resolve index
        self.widget.set_num_patterns(len(npulse_per_frame))

        # 2. Finalize
        self.widget.set_parameters(*self._get_pattern(npulse_per_frame))

    def _get_pattern(self, npulse_per_frame=None):
        node = get_binding_value(self.proxy)

        if npulse_per_frame is None:
            npulse_per_frame, _ = get_array_data(
                node.nPulsePerFrame, default=np.array([[]], dtype=np.uint16))
        nframe = npulse_per_frame.shape[1]

        if npulse_per_frame.size:
            npulse_per_frame = (npulse_per_frame.sum(axis=0) if self._is_union
                                else npulse_per_frame[self._index])

        return nframe, npulse_per_frame

    def _enable_union(self, enabled):
        self._is_union = enabled
        self.widget.set_parameters(*self._get_pattern())

    def __index_changed(self):
        self.widget.set_parameters(*self._get_pattern())

    def _update_index(self, selected):
        self.trait_set(_index=selected - NUM_PATTERNS_START)
