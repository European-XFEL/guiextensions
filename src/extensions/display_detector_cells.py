from enum import Enum

import numpy as np
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPen
from qtpy.QtWidgets import (
    QAction, QDialog, QDialogButtonBox, QFormLayout, QGraphicsRectItem,
    QGraphicsScene, QGraphicsView, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget)
from traits.api import Bool, Instance, Int

from karabo.common.api import State
from karabogui.binding.api import (
    BaseBinding, PropertyProxy, StringBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.fonts import get_font_size_from_dpi

from .models.api import DetectorCellsModel, MultipleDetectorCellsModel
from .utils import get_array_data

GRAY = QColor(127, 127, 127, 255)
BLUE = QColor(31, 119, 180, 255)
ORANGE = QColor(255, 127, 14, 255)
RED = QColor(255, 204, 203, 255)
NOPEN = QPen(Qt.transparent)

ALGN_CENTER = 1
ALGN_TOP = 0
ALGN_BOTTOM = 2
ALGN_LEFT = 0
ALGN_RIGHT = 2

OFFSET_H = 40
OFFSET_V = 40
GAP_H = 3
GAP_V = 3
SIDE = 12
TICK_LEN = 6
STRIDE_H = SIDE + GAP_H
STRIDE_V = SIDE + GAP_H
STRIDE_LEGEND = 70
LEGEND_MIN_HEIGHT = OFFSET_V + 5 * STRIDE_V - GAP_V
LEGEND_MIN_WIDTH = OFFSET_H + 21 * STRIDE_H - GAP_H

NUM_PATTERNS_START = 1
DEFAULT_NUM_PATTERNS = NUM_PATTERNS_START + 0  # no pattern


class Location(Enum):
    BOTTOM = 'bottom'
    RIGHT = 'right'


class CellStyle(Enum):
    UNUSED = (NOPEN, QBrush(GRAY), None)
    DARK = (NOPEN, QBrush(BLUE), None)
    LIT = (NOPEN, QBrush(ORANGE), None)
    LIT_BLOCKED = (NOPEN, QBrush(ORANGE, Qt.Dense4Pattern), BLUE)

    @property
    def brush(self):
        return self.value[1]

    @property
    def pen(self):
        return self.value[0]

    @property
    def bgcolor(self):
        return self.value[2]

    @classmethod
    def index(cls, pos):
        return list(cls)[pos]


class QGraphicsCellItem(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bg_color = Qt.transparent

    def paint(self, painter, option, widget):
        if self._bg_color != Qt.transparent:
            painter.setBrush(QBrush(self._bg_color))
            painter.setPen(QPen(Qt.transparent))
            painter.drawRect(self.rect())
        super().paint(painter, option, widget)

    def setBackgroundColor(self, color):
        self._bg_color = (color if color is not None
                          else Qt.transparent)


def draw_cell(scene, x, y, style=CellStyle.UNUSED):
    cell = QGraphicsCellItem(x, y, SIDE, SIDE)
    cell.setPen(style.pen)
    cell.setBrush(style.brush)
    cell.setBackgroundColor(style.bgcolor)
    scene.addItem(cell)
    return cell


def set_cell_style(cell, style):
    cell.setPen(style.pen)
    cell.setBrush(style.brush)
    cell.setBackgroundColor(style.bgcolor)


class DetectorCellsWidget(QWidget):

    nrow = 0
    ncol = 0

    def __init__(self, rows=0, cols=0,
                 legend_location=Location.BOTTOM,
                 parent=None):
        super().__init__(parent)
        self.cells = []

        self.nfrm = 0
        self.cell_style_codes = np.zeros(self.nfrm, dtype=np.uint16)

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

        # Finalize
        self.legend_location = legend_location
        self.set_cells(rows, cols, update=False)

    def set_legend_location(self, location):
        self.legend_location = Location(location)

        # Redraw
        self.set_cells(rows=self.nrow, columns=self.ncol)

    def set_cells(self, rows, columns, update=True):
        self.nrow, self.ncol = rows, columns
        width = OFFSET_H + columns * STRIDE_H - GAP_H
        height = OFFSET_V + rows * STRIDE_V - GAP_V

        if self.legend_location == Location.RIGHT:
            offset_w, offset_h = (114, 10)
            height = max(height, LEGEND_MIN_HEIGHT)
        else:
            offset_w, offset_h = (10, 40)
            width = max(width, LEGEND_MIN_WIDTH)

        self.scene = QGraphicsScene(0, 0, width + offset_w, height + offset_h)
        self.view.setScene(self.scene)

        self.draw_cells()
        self.draw_legends()

        if update:
            # Store parameters temporarily
            nfrm, cell_style_codes = self.nfrm, self.cell_style_codes

            # Reset to default values
            self.nfrm = 0
            self.cell_style_codes = np.zeros(self.nfrm, dtype=np.uint16)

            # Set the parameters back and trigger painting
            self.set_parameters(nfrm, 0, cell_style_codes)

    def add_text(self, text, x, y, va=ALGN_CENTER, ha=ALGN_CENTER,
                 font='Courier', size=9):
        t = self.scene.addText(text)

        size = get_font_size_from_dpi(size)
        t.setFont(QFont(font, size, QFont.Light))

        brect = t.boundingRect()
        t.setPos(x - ha * brect.width() / 2, y - va * brect.height() / 2)

        return t

    def draw_cells(self):
        self.cells.clear()

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

                self.cells.append(draw_cell(self.scene, x, y))
                x += STRIDE_H

            y += STRIDE_V

    def draw_legends(self):
        draw_map = {
            Location.BOTTOM: self._draw_legends_bottom,
            Location.RIGHT: self._draw_legends_right}
        draw = (draw_map.get(self.legend_location)
                or draw_map.get(Location.BOTTOM))
        draw()

    def _draw_legends_right(self):
        x = OFFSET_H + self.ncol * STRIDE_H + 15

        y = OFFSET_V
        ypos = y + SIDE / 2
        draw_cell(self.scene, x, y, CellStyle.UNUSED)
        self.add_text('UNUSED', x + SIDE, ypos, ha=ALGN_LEFT)

        y += STRIDE_V
        ypos = y + SIDE / 2
        draw_cell(self.scene, x, y, CellStyle.DARK)
        self.add_text('DARK', x + SIDE, ypos, ha=ALGN_LEFT)

        y += STRIDE_V
        ypos = y + SIDE / 2
        draw_cell(self.scene, x, y, CellStyle.LIT)
        self.nlit_legend = self.add_text("LIT:    0",
                                         x + SIDE, ypos, ha=ALGN_LEFT)

        y += STRIDE_V * 2
        ypos = y + SIDE / 2
        self.ncell_legend = self.add_text("USED:   0",
                                          x + SIDE, ypos, ha=ALGN_LEFT)

    def _draw_legends_bottom(self):
        y = OFFSET_V + STRIDE_V * (self.nrow + 1)
        ypos = y + SIDE / 2

        x = OFFSET_H
        draw_cell(self.scene, x, y, CellStyle.UNUSED)
        self.add_text('UNUSED', x + SIDE, ypos, ha=ALGN_LEFT)

        x += STRIDE_LEGEND
        draw_cell(self.scene, x, y, CellStyle.DARK)
        self.add_text('DARK', x + SIDE, ypos, ha=ALGN_LEFT)

        x += STRIDE_LEGEND
        draw_cell(self.scene, x, y, CellStyle.LIT)
        self.nlit_legend = self.add_text("LIT:    0", x + SIDE, ypos,
                                         ha=ALGN_LEFT)

        x = max(OFFSET_H + self.ncol * STRIDE_H - GAP_H, LEGEND_MIN_WIDTH)
        self.ncell_legend = self.add_text("USED:   0", x, ypos, ha=ALGN_RIGHT)

    def set_parameters(self, nfrm, nlit, cell_style_codes):
        if len(cell_style_codes) != nfrm:
            cell_style_codes = np.zeros(nfrm, dtype=np.uint16)

        # Determine changed pulses
        nsmall = min(min(nfrm, self.nfrm), len(self.cells))
        nlarge = min(max(nfrm, self.nfrm), len(self.cells))
        overlap_diff = np.flatnonzero(self.cell_style_codes[:nsmall]
                                      != cell_style_codes[:nsmall])
        oneside_diff = np.arange(nsmall, nlarge)
        changed_cells = np.concatenate([overlap_diff, oneside_diff])

        # Update cells
        for i in changed_cells:
            cell = self.cells[i]
            style = CellStyle.index(cell_style_codes[i] if i < nfrm else 0)
            set_cell_style(cell, style)

        # Display indicators if number of incoming used cells is greater than
        # the number of displayed cells
        bg_color, text_color = Qt.white, Qt.black
        if nfrm > len(self.cells):
            bg_color, text_color = RED, Qt.red
        self.view.setBackgroundBrush(QBrush(bg_color))
        self.ncell_legend.setDefaultTextColor(text_color)

        # Finalize
        self.nfrm = nfrm
        self.cell_style_codes = cell_style_codes

        self.ncell_legend.setPlainText(f"USED: {nfrm:3d}")
        self.nlit_legend.setPlainText(f"LIT:  {nlit:3d}")

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


def _is_state(binding):
    return (isinstance(binding, StringBinding)
            and binding.display_type == "State")


class BaseDetectorCellsController(BaseBindingController):
    """Base class for the detector cells controller.

    This enables support of the old schema (single pattern)
    and the new schema (multiple pattern) using the same widget."""

    _is_union = Bool(False)
    _index = Int
    _shutter_open = Bool(True)

    _shutter_proxy = Instance(PropertyProxy)

    def create_widget(self, parent):
        rows, cols = self.model.rows, self.model.columns
        widget = DetectorCellsWidget(rows=rows, cols=cols, parent=parent)
        widget.set_legend_location(self.model.legend_location)

        # Configure shape
        shape_action = QAction("Cells shape", widget)
        shape_action.triggered.connect(self._configure_cells_shape)
        widget.addAction(shape_action)

        # Configure legend location
        legend_action = QAction("Legend location", widget)
        legend_action.triggered.connect(self._configure_legend_location)
        widget.addAction(legend_action)

        return widget

    def add_proxy(self, proxy):
        binding = proxy.binding

        # We postpone adding the proxy if it is still None:
        # This is usual for properties of offline devices
        if binding is None:
            return True

        if _is_state(binding) and self._shutter_proxy is None:
            self._shutter_proxy = proxy
            return True

    def binding_update(self, proxy):
        self.add_proxy(proxy)
        self.value_update(proxy)

    def value_update(self, proxy):
        value = get_binding_value(proxy)
        if value is None:
            return

        if proxy is self._shutter_proxy:
            self._shutter_open = State(value).isDerivedFrom(State.ACTIVE)
            node = get_binding_value(self.proxy)
        elif proxy is self.proxy:
            node = value
            value = self._shutter_open

        # 0. Get values
        npulse_per_frame = self._get_npulse_per_frame(node)

        # 1. Resolve index
        self.widget.set_num_patterns(self._get_num_pattern(npulse_per_frame))

        # 2. Finalize
        self.widget.set_parameters(*self._get_pattern(npulse_per_frame))

    def _get_cell_style_codes(self, npulse_per_frame, shutter_open):
        litframes = (npulse_per_frame != 0).astype(int)
        return litframes + 1 + int(not shutter_open) * litframes

    def _get_pattern(self, npulse_per_frame=None):
        raise NotImplementedError

    def _get_npulse_per_frame(self, node):
        raise NotImplementedError

    def _get_num_pattern(self, npulse_per_frame):
        raise NotImplementedError

    def _configure_cells_shape(self):
        config = {"rows": self.model.rows, "columns": self.model.columns}

        content, ok = CellsShapeDialog.get(config, parent=self.widget)
        if not ok:
            return

        self.model.trait_set(**content)
        self.widget.set_cells(**content)

    def _configure_legend_location(self):
        locations = [loc.value for loc in Location]
        index = locations.index(self.model.legend_location)

        location, ok = QInputDialog.getItem(self.widget,
                                            "Set legend location",
                                            "Legend location:",
                                            locations, index, False)
        if not ok:
            return

        self.model.legend_location = location
        self.widget.set_legend_location(location)


@register_binding_controller(
    ui_name='Detector Cells Widget',
    klassname='DetectorCells',
    binding_type=BaseBinding,
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

    def _get_npulse_per_frame(self, node):
        nfrm = get_binding_value(node.nFrame, default=0)
        npulse_per_frame = get_binding_value(
            node.nPulsePerFrame, default=np.zeros(nfrm, np.uint16))
        return npulse_per_frame

    def _get_num_pattern(self, npulse_per_frame):
        return 0

    def _get_pattern(self, npulse_per_frame=None):
        if npulse_per_frame is None:
            node = get_binding_value(self.proxy)
            npulse_per_frame = self._get_npulse_per_frame(node)
        nfrm = len(npulse_per_frame)
        nlit = np.sum(npulse_per_frame > 0)
        pattern = self._get_cell_style_codes(
            npulse_per_frame, self._shutter_open)
        return nfrm, nlit, pattern


@register_binding_controller(
    ui_name='Detector Cells Widget',
    klassname='MultipleDetectorCells',
    binding_type=BaseBinding,
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

    def _get_npulse_per_frame(self, node):
        npulse_per_frame, _ = get_array_data(
            node.nPulsePerFrame, default=np.array([[]], dtype=np.uint16))
        return npulse_per_frame

    def _get_num_pattern(self, npulse_per_frame):
        return len(npulse_per_frame)

    def _get_pattern(self, npulse_per_frame=None):
        if npulse_per_frame is None:
            node = get_binding_value(self.proxy)
            npulse_per_frame = self._get_npulse_per_frame(node)

        nframe = npulse_per_frame.shape[1]

        if npulse_per_frame.size:
            npulse_per_frame = (npulse_per_frame.sum(axis=0) if self._is_union
                                else npulse_per_frame[self._index])

        nlit = np.sum(npulse_per_frame > 0)
        pattern = self._get_cell_style_codes(
            npulse_per_frame, self._shutter_open)
        return nframe, nlit, pattern

    def _enable_union(self, enabled):
        self._is_union = enabled
        self.widget.set_parameters(*self._get_pattern())

    def __index_changed(self):
        self.widget.set_parameters(*self._get_pattern())

    def _update_index(self, selected):
        self.trait_set(_index=selected - NUM_PATTERNS_START)


class CellsShapeDialog(QDialog):
    """"""
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.setModal(False)
        self.setWindowTitle("Set cells shape")

        self.rows_spinbox = rows_spinbox = QSpinBox()
        rows_spinbox.setMinimum(0)
        rows_spinbox.setValue(config['rows'])

        self.cols_spinbox = cols_spinbox = QSpinBox()
        cols_spinbox.setMinimum(0)
        cols_spinbox.setValue(config['columns'])

        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(5)
        form.addRow("Rows:", rows_spinbox)
        form.addRow("Columns:", cols_spinbox)

        # Add button boxes
        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Finalize widget
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.addLayout(form)
        layout.addWidget(button_box)
        self.setLayout(layout)

    @staticmethod
    def get(configuration, parent=None):
        dialog = CellsShapeDialog(configuration, parent)
        result = dialog.exec_() == QDialog.Accepted
        content = {"rows": dialog.rows,
                   "columns": dialog.columns}
        return content, result

    @property
    def rows(self):
        return self.rows_spinbox.value()

    @property
    def columns(self):
        return self.cols_spinbox.value()
