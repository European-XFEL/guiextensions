from functools import reduce

import numpy as np
from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor, QFont, QPainter, QPen
from qtpy.QtWidgets import QGraphicsScene, QGraphicsView, QGridLayout, QWidget
from traits.api import Array, HasStrictTraits, Instance, on_trait_change, Tuple

from karabogui.binding.api import get_binding_value, WidgetNodeBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.fonts import get_font_size_from_dpi
from karabogui.util import generateObjectName

from extensions.models.simple import DynamicPulseIdMapModel, PulseIdMapModel

GRAY = QColor(178, 178, 178, 60)
YELLOW = QColor(255, 194, 10, 200)
BLUE = QColor(12, 123, 220)

BRUSH_EMPTY = QBrush(GRAY)
BRUSH_FEL = QBrush(YELLOW)
BRUSH_PPL = QBrush(BLUE)

PEN_DET = QPen(BLUE, 2)
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
        self.scene.addRect(rect.translated(h + 160, v),
                           PEN_DET, QBrush(Qt.transparent))
        self.add_text('DET', (h + 180, v - side/4))
        self.add_ppl(h + 240 - PPL_SIZE / 2, v - PPL_SIZE / 2 + side / 2,
                     visible=True)
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
    klassname='PulseIdMap',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|PulseId-Map'),
    priority=0, can_show_nothing=False)
class PulseIdMap(BaseBindingController):
    """Show a matrix representing the internal XFEL pulses

    This widget is used with a special widget node type: PulseId-Map.
    In this node we expect to have three properties,
    `fel` `ppl` and `det`, which will be set whenever
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


# -----------------------------------------------------------------------------

NUM_PULSES = 2700


class PulsePattern(HasStrictTraits):
    fel = Array(value=np.zeros(NUM_PULSES, dtype=np.bool_))
    ppl = Array(value=np.zeros(NUM_PULSES, dtype=np.bool_))
    det = Array(value=np.zeros(NUM_PULSES, dtype=np.bool_))

    fel_index = Array
    ppl_index = Array
    det_index = Array

    fel_diff = Array
    ppl_diff = Array
    det_diff = Array
    diff = Array

    grid_specs = Tuple(0, 0, 0)  # min, max, width
    grid = Array

    def set_node(self, node):
        # Get values
        self.fel = get_binding_value(node.fel, default=[])
        self.ppl = get_binding_value(node.ppl, default=[])
        self.det = get_binding_value(node.fel, default=[])

        # Recalculate grid
        self.grid_specs = self._calc_grid_specs()

        # Update diff for external updates
        diff = reduce(np.union1d,
                      (self.fel_diff, self.ppl_diff, self.det_diff))
        if diff.size:
            self.diff = diff

    def _fel_changed(self, old, new):
        self.fel_diff = np.where(old != new)[0]
        self.fel_index = self._calc_index(new)

    def _ppl_changed(self, old, new):
        self.ppl_diff = np.where(old != new)[0]
        self.ppl_index = self._calc_index(new)

    def _det_changed(self, old, new):
        self.det_diff = np.where(old != new)[0]
        self.det_index = self._calc_index(new)

    def _grid_specs_changed(self, specs):
        min_value, max_value, grid_size = specs
        self.grid = np.arange(min_value, max_value).reshape((-1, grid_size))

    def _calc_index(self, pattern):
        return np.argwhere(pattern).squeeze()

    def _calc_grid_specs(self):
        def round_down(value, nearest=10):
            return round(value / nearest) * nearest

        # Get grid count
        diff = np.hstack((np.diff(self.fel_index),
                          np.diff(self.ppl_index),
                          np.diff(self.det_index)))
        values, counts = np.unique(diff, return_counts=True)
        grid_size = values[counts.argmax()]

        # Get min and max values
        min_value = round_down(self.fel_index[0],
                               nearest=grid_size) - grid_size
        max_value = max(self.fel_index[-1],
                        self.ppl_index[-1],
                        self.det_index[-1])
        max_value = round_down(max_value, nearest=grid_size) + grid_size

        return min_value, max_value, grid_size


class DynamicPulseIdMapWidget(QWidget):
    """Show a matrix representing the internal XFEL pulses

    The color coded matrix shows which pulses in the train contain
    fel light, ppl light and if a detector is acquiring this pulse.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 500)  # min-size of the widget
        # Graphics items
        self.pulses = []
        self.fel_legend = None
        self.ppl_legend = None
        self.det_legend = None

        grid = QGridLayout(self)
        self.view = QGraphicsView()
        object_name = generateObjectName(self.view)
        self.view.setObjectName(object_name)
        self.view.setStyleSheet("QFrame#{name}".format(name=object_name) +
                                "{ border: 20px solid white; }")
        grid.addWidget(self.view)
        self.view.setRenderHints(QPainter.Antialiasing)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        self.draw_matrix(grid=np.empty(shape=(0, 0)))

    def clear(self):
        self.pulses = [None] * NUM_PULSES
        self.fel_legend = None
        self.ppl_legend = None
        self.det_legend = None
        self.scene.clear()

    def add_text(self, text, pos=(0, 0), font='Courier', size=9):
        size = get_font_size_from_dpi(size)
        t = self.scene.addText(text)
        t.setPos(*pos)
        t.setFont(QFont(font, size, QFont.Light))
        return t

    def add_ppl(self, x, y, visible=False):
        """Add ellipse for PPL
        """
        ellipse = self.scene.addEllipse(x, y, PPL_SIZE, PPL_SIZE)
        ellipse.setBrush(BRUSH_PPL)
        ellipse.setPen(PEN_EMPTY)
        ellipse.setVisible(visible)
        return ellipse

    def draw_matrix(self, grid):
        # Clear items from scene
        self.clear()
        rows, cols = grid.shape

        offset_h, offset_v, gap_h, gap_v, side = 40, 30, 1, 5, 12
        rect = QRectF(0, 0, side, side)
        for row in range(rows):
            self.add_text(f'{grid[row][0]}'.rjust(4, ' '),
                          (0, offset_v + row * (side + gap_v) - side/4))

            for col in range(cols):
                ref_h = offset_h + col * (side + gap_h)
                ref_v = offset_v + row * (side + gap_v)
                pulse_num = grid[row][col]

                # add labels
                if col % 10 == 0:
                    self.add_text(f'{col}', (ref_h - side / 2, 0))
                    self.add_text('❘', (ref_h - side / 4,
                                        offset_v / 2 - side / 2))

                # background representing fel/no-fel
                fel = self.scene.addRect(rect.translated(ref_h, ref_v),
                                         PEN_EMPTY,
                                         BRUSH_EMPTY)
                fel.setToolTip(f'Pulse {pulse_num}')
                # center dot: ppl/no-ppl
                ppl = self.add_ppl(ref_h + side / 2 - PPL_SIZE / 2,
                                   ref_v + side / 2 - PPL_SIZE / 2)
                self.pulses[pulse_num] = (fel, ppl)

        # add legend
        h, v = offset_h, offset_v + (rows + gap_h) * (side + gap_v)
        legend_pos = v - side/4
        self.scene.addRect(rect.translated(h, v), PEN_EMPTY, GRAY)
        self.add_text('EMPTY', (h + 20, legend_pos))
        self.scene.addRect(rect.translated(h + 80, v), PEN_EMPTY, BRUSH_FEL)
        self.add_text('FEL', (h + 100, legend_pos))
        self.scene.addRect(rect.translated(h + 160, v),
                           PEN_DET, QBrush(Qt.transparent))
        self.add_text('DET', (h + 180, legend_pos))
        self.add_ppl(h + 240 - PPL_SIZE / 2, v - PPL_SIZE / 2 + side / 2,
                     visible=True)
        self.add_text('PPL', (h + 260, legend_pos))

        horz_pos, gap = h + 400, side + gap_v
        self.fel_legend = self.add_text("FEL: 0",
                                        (horz_pos, legend_pos))
        self.ppl_legend = self.add_text("PPL: 0",
                                        (horz_pos, legend_pos + gap))
        self.det_legend = self.add_text("DET: 0",
                                        (horz_pos, legend_pos + gap * 2))

    def set_parameter(self, *, fel, ppl, det, diff=None):
        if diff is None:
            diff = np.arange(NUM_PULSES)
        for idx in diff:
            rect_items = self.pulses[idx]
            if rect_items is None:
                continue

            w_fel, w_ppl = rect_items
            tooltip = [f'Pulse {idx}']

            # Update FEL
            brush = BRUSH_EMPTY
            fel_idx, = np.nonzero(fel == idx)
            if fel_idx.size:
                brush = BRUSH_FEL
                tooltip.append(f'FEL: #{fel_idx[0] + 1}')
            w_fel.setBrush(brush)

            # Update PPL
            ppl_idx, = np.nonzero(ppl == idx)
            visible = bool(ppl_idx.size)
            if visible:
                tooltip.append(f'PPL: #{ppl_idx[0] + 1}')
            w_ppl.setVisible(visible)

            # Update DET
            pen = PEN_EMPTY
            det_idx, = np.nonzero(det == idx)
            if det_idx.size:
                pen = PEN_DET
                tooltip.append(f'DET: #{det_idx[0] + 1}')
            w_fel.setPen(pen)

            w_fel.setToolTip('\n'.join(tooltip))

        self.fel_legend.setPlainText(f"FEL: {fel.size}")
        self.ppl_legend.setPlainText(f"PPL: {ppl.size}")
        self.det_legend.setPlainText(f"DET: {det.size}")
        self.update()


@register_binding_controller(
    ui_name='Dynamic PulseId-Map Widget',
    klassname='DynamicPulseIdMap',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|PulseId-Map'),
    priority=0, can_show_nothing=False)
class DynamicPulseIdMap(BaseBindingController):
    """Show a matrix representing the internal XFEL pulses

    This widget is used with a special widget node type: PulseId-Map.
    In this node we expect to have three properties, `fel` `ppl` and `det`,
    which will be set whenever fel, ppl or det has light/frame
    for a specified pulse.
    """
    model = Instance(DynamicPulseIdMapModel, args=())
    _pulse_pattern = Instance(PulsePattern, args=())

    def create_widget(self, parent):
        widget = DynamicPulseIdMapWidget(parent)
        return widget

    def value_update(self, proxy):
        if proxy.value is None:
            return
        self._pulse_pattern.set_node(proxy.value)

    @on_trait_change("_pulse_pattern.grid")
    def _update_grid(self, grid):
        self.widget.draw_matrix(grid)

    @on_trait_change("_pulse_pattern.diff")
    def _update_pattern(self):
        if self.widget is None:
            return

        pattern = self._pulse_pattern
        self.widget.set_parameter(fel=pattern.fel_index,
                                  ppl=pattern.ppl_index,
                                  det=pattern.det_index,
                                  diff=pattern.diff)
