import numpy as np
from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPen
from qtpy.QtWidgets import QGraphicsScene, QGraphicsView, QGridLayout, QWidget
from traits.api import Instance

from karabogui.binding.api import WidgetNodeBinding, get_binding_value
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.fonts import get_font_size_from_dpi

from .models.api import DetectorCellsModel

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
                              == npulse_per_frame[:nsmall])[0]
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


@register_binding_controller(
    ui_name='Detector Cells Widget',
    klassname='DetectorCells',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|DetectorCells'),
    priority=0, can_show_nothing=False)
class DetectorCells(BaseBindingController):
    """Show a matrix representing the detector memory cells

    This widget is used with a special widget node type: DetectorCells. In this
    node we expect to have two properties, `nFrame` and `nPulsePerFrame`.
    """
    model = Instance(DetectorCellsModel, args=())

    def create_widget(self, parent):
        widget = DetectorCellsWidget(parent)
        return widget

    def value_update(self, proxy):
        node = get_binding_value(proxy)
        if node is None:
            return

        nfrm = get_binding_value(node.nFrame, default=0)
        npulse_per_frame = get_binding_value(
            node.nPulsePerFrame, default=np.zeros(nfrm, np.uint16))
        self.widget.set_parameters(nfrm, npulse_per_frame)
