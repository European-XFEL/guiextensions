import numpy as np
from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPen
from qtpy.QtWidgets import QGraphicsScene, QGraphicsView, QGridLayout, QWidget
from traits.api import Instance

from karabogui.binding.api import WidgetNodeBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.fonts import get_font_size_from_dpi

from .models.simple import PulseIdMapModel

GRAY = QColor(178, 178, 178, 100)
ORANGE = QColor(243, 146, 0, 150)
RED = QColor(Qt.red)

BRUSH_EMPTY = QBrush(GRAY)
BRUSH_FEL = QBrush(ORANGE)
BRUSH_PPL = QBrush(RED)

PEN_DET = QPen(RED, 2)
PEN_EMPTY = QPen(Qt.transparent)

PPL_SIZE = 4  # circle size in pixels


class PulseIdMapWidget(QWidget):
    """Show a matrix representing the internal XFEL pulses

    The color coded matrix shows which pulses in the train contain
    fel light, ppl light and if a detector is acquiring this pulse.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 500)  # min-size of the widget
        self.columns = 100  # num of columns in grid
        self.rows = 27  # num of rows in grid
        self.pulses = []
        # Pulses positions
        self.fel = np.zeros(2700, dtype=np.bool_)
        self.ppl = np.zeros(2700, dtype=np.bool_)
        self.det = np.zeros(2700, dtype=np.bool_)

        grid = QGridLayout(self)
        self.view = QGraphicsView()
        grid.addWidget(self.view)
        self.view.setRenderHints(QPainter.Antialiasing)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.draw_matrix()

    def add_text(self, text, pos=(0, 0), font='Courier', size=9):
        size = get_font_size_from_dpi(size)
        t = self.scene.addText(text)
        t.setPos(*pos)
        t.setFont(QFont(font, size, QFont.Light))

    def add_ppl(self, x, y, visible=False):
        """Add ellipse for PPL
        """
        ellipse = self.scene.addEllipse(x, y, PPL_SIZE, PPL_SIZE)
        ellipse.setBrush(BRUSH_PPL)
        ellipse.setPen(PEN_EMPTY)
        ellipse.setVisible(visible)
        return ellipse

    def draw_matrix(self):
        offset_h, offset_v, gap_h, gap_v, side = 40, 30, 1, 5, 12
        rect = QRectF(0, 0, side, side)
        for row in range(self.rows):
            self.add_text(f'{row * 100}'.rjust(4, ' '),
                          (0, offset_v + row * (side + gap_v) - side/4))

            for col in range(self.columns):
                ref_h = offset_h + col * (side + gap_h)
                ref_v = offset_v + row * (side + gap_v)

                # add labels
                if col % 20 == 0:
                    self.add_text(f'{col}', (ref_h - side / 2, 0))
                    self.add_text('❘', (ref_h - side / 4,
                                        offset_v / 2 - side / 2))

                # background representing fel/no-fel
                fel = self.scene.addRect(rect.translated(ref_h, ref_v),
                                         PEN_EMPTY,
                                         BRUSH_EMPTY)
                fel.setToolTip(f'Pulse {row * self.columns + col}'
                               '\nFEL: False\nPPL: False\nDET: False')
                # center dot: ppl/no-ppl
                ppl = self.add_ppl(ref_h + side / 2 - PPL_SIZE / 2,
                                   ref_v + side / 2 - PPL_SIZE / 2)
                self.pulses.append((fel, ppl))

        # add legend
        h, v = offset_h, offset_v + (self.rows + gap_h) * (side + gap_v)
        self.scene.addRect(rect.translated(h, v), PEN_EMPTY, GRAY)
        self.add_text('EMPTY', (h + 20, v - side/4))
        self.scene.addRect(rect.translated(h + 80, v), PEN_EMPTY, BRUSH_FEL)
        self.add_text('FEL', (h + 100, v - side/4))
        self.scene.addRect(rect.translated(h + 160, v), PEN_DET, QBrush(Qt.transparent))
        self.add_text('DET', (h + 180, v - side/4))
        self.add_ppl(h + 240 - PPL_SIZE / 2, v - PPL_SIZE / 2 + side / 2, visible=True)
        self.add_text('PPL', (h + 260, v - side/4))

    def set_parameter(self, fel, ppl, det):
        fel = fel if (fel.size == 2700) else np.zeros(2700, dtype=np.bool_)
        ppl = ppl if (ppl.size == 2700) else np.zeros(2700, dtype=np.bool_)
        det = det if (det.size == 2700) else np.zeros(2700, dtype=np.bool_)

        fel_diff = np.where(fel != self.fel)[0]
        ppl_diff = np.where(ppl != self.ppl)[0]
        det_diff = np.where(det != self.det)[0]
        self.fel, self.ppl, self.det = fel, ppl, det

        for idx in sorted(set(fel_diff).union(ppl_diff, det_diff)):
            w_fel, w_ppl = self.pulses[idx]

            w_fel.setBrush(BRUSH_FEL if fel[idx] else BRUSH_EMPTY)
            w_fel.setPen(PEN_DET if det[idx] else PEN_EMPTY)
            w_ppl.setVisible(ppl[idx])

            w_fel.setToolTip(
                f'Pulse {idx}'
                f'\nFEL: {fel[idx]}'
                f'\nPPL: {ppl[idx]}'
                f'\nDET: {det[idx]}'
            )

        self.update()


@register_binding_controller(
    ui_name='PulseId-Map Widget',
    klassname='PulseId-Map',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|PulseId-Map'),
    priority=0, can_show_nothing=False)
class PulseIdMap(BaseBindingController):
    """Show a matrix representing the internal XFEL pulses

    This widget is used with a special widget node type: PulseId-Map. In this node we
    expect to have three properties, `fel` `ppl` and `det`, which will be set whenever
    fel, ppl or det has light/frame for a specified pulse.
    """
    model = Instance(PulseIdMapModel, args=())

    def create_widget(self, parent):
        widget = PulseIdMapWidget(parent)
        return widget

    def value_update(self, proxy):
        if proxy.value is None:
            return

        self.widget.set_parameter(
            proxy.value.fel.value,
            proxy.value.ppl.value,
            proxy.value.det.value
        )
