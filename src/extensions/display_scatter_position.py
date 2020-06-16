#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on June 20, 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from collections import deque

import numpy as np
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAction, QInputDialog
from pyqtgraph import EllipseROI, ROI
from traits.api import Instance

from karabo.common.scenemodel.api import build_model_config
from karabogui import icons
from karabogui.binding.api import WidgetNodeBinding
from karabogui.controllers.api import (
    with_display_type, BaseBindingController, register_binding_controller)
from karabogui.graph.common.api import create_tool_button, make_pen
from karabogui.graph.plots.api import KaraboPlotView

from .models.simple import ScatterPositionModel

BUTTON_SIZE = (52, 32)
MAX_NUM_POINTS = 1000

MIN_POINT_SIZE = 0.1
MAX_POINT_SIZE = 10.0

SILVER = QColor(192, 192, 192)
FIREBRICK = QColor(178, 34, 34)


class Ellipse(EllipseROI):
    def __init__(self, pos, size, pen=make_pen('r'), ):
        self.path = None
        ROI.__init__(self, pos, size, pen=pen, movable=False,
                     removable=False)
        self.sigRegionChanged.connect(self._clearPath)

    def setValue(self, pos, size):
        self.setPos(pos, update=False)
        self.setSize(size, update=True)


@register_binding_controller(
    ui_name='Scatter Position Widget',
    klassname='ScatterPosition',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|ScatterPosition'),
    priority=0, can_show_nothing=False)
class DisplayScatterPosition(BaseBindingController):
    model = Instance(ScatterPositionModel, args=())

    _x_values = Instance(deque)
    _y_values = Instance(deque)

    _plot = Instance(object)
    _ellipse = Instance(object)

    def create_widget(self, parent):

        widget = KaraboPlotView(parent=parent)
        widget.add_cross_target()
        toolbar = widget.add_toolbar()

        _btn_reset = create_tool_button(
            checkable=False,
            icon=icons.reset,
            tooltip="Reset the plot",
            on_clicked=self._reset_plot)
        try:
            toolbar.add_button(name="reset", button=_btn_reset)
            # GUI Changes
        except Exception:
            toolbar.add_button(button=_btn_reset)
        widget.stateChanged.connect(self._change_model)

        model = self.model
        self._x_values = deque(maxlen=model.maxlen)
        self._y_values = deque(maxlen=model.maxlen)

        self._plot = widget.add_scatter_item()

        self._ellipse = Ellipse((0, 0), (0.1, 0.1))
        widget.plotItem.addItem(self._ellipse)
        # assigning proxy is safe and wanted here!
        widget.restore(build_model_config(self.model))

        self._plot.setSize(self.model.psize)

        deque_action = QAction("Queue Size", widget)
        deque_action.triggered.connect(self._configure_deque)
        widget.addAction(deque_action)

        point_size_action = QAction("Point Size", widget)
        point_size_action.triggered.connect(self._configure_point_size)
        point_size_action.setIcon(icons.scatter)
        widget.addAction(point_size_action)

        return widget

    # ----------------------------------------------------------------

    def value_update(self, proxy):
        if proxy.value is None:
            return
        # NOTE: We utilize that all values are set at once in the pipeline!
        pos_x = proxy.value.posX.value
        pos_y = proxy.value.posY.value

        self._x_values.append(pos_x)
        self._y_values.append(pos_y)
        pos = (float(np.mean(self._x_values)), float(np.mean(self._y_values)))
        size = (float(np.std(self._x_values)), float(np.std(self._y_values)))
        self._ellipse.setValue(pos, size)
        self._plot.setData(self._x_values, self._y_values)

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**content)

    def _reset_plot(self):
        self._x_values.clear()
        self._y_values.clear()
        self._plot.clear()

    def _configure_deque(self):
        maxlen, ok = QInputDialog.getInt(self.widget, 'Number of Values',
                                         'Maxlen:', self.model.maxlen, 5,
                                         MAX_NUM_POINTS)
        if ok:
            self._last_x_value = None
            self._x_values, self._y_values = None, None
            self._x_values = deque(maxlen=maxlen)
            self._y_values = deque(maxlen=maxlen)

            self.model.maxlen = maxlen

    def _configure_point_size(self):
        psize, ok = QInputDialog.getDouble(self.widget, 'Size of points',
                                           'Pointsize:', self.model.psize,
                                           MIN_POINT_SIZE, MAX_POINT_SIZE)
        if ok:
            self._plot.setSize(psize)
            self.model.psize = psize
