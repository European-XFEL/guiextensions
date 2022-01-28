#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on October 25, 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from itertools import cycle

import numpy as np
from pyqtgraph import PlotDataItem, mkPen
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QAction, QInputDialog
from traits.api import Instance, List, WeakRef

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabogui.binding.api import NDArrayBinding, VectorNumberBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)
from karabogui.controllers.arrays import get_array_data
from karabogui.graph.plots.api import (
    KaraboPlotView, generate_baseline, generate_down_sample, get_view_range)

from .models.api import DynamicGraphModel

MAX_CURVES = 20
START_COLOR = QColor(0, 51, 102)
STOP_COLOR = QColor(153, 204, 255)


def get_pen_cycler(start_color, stop_color, num):
    """Create a color gradient between two colors

    :param start_color: An rgb tuple or `QColor` for the start color
    :param stop_color: An rgb tuple or `QColor` for the stop color
    :param num: the number of intermediate colors

    :returns: Full list of rgb colors
    """

    def _create_gradient(start, stop, n=10):
        start = start.getRgb() if isinstance(start, QColor) else start
        stop = stop.getRgb() if isinstance(stop, QColor) else stop

        assert len(start) == len(stop), "Color space must be of same length"
        color_space = len(start)
        colors = [start]
        for num in range(1, n):
            percent = float(num / (n - 1))
            rgb_color = tuple(int(start[j] + percent * (stop[j] - start[j]))
                              for j in range(color_space))
            colors.append(rgb_color)

        return colors

    colors = _create_gradient(start_color, stop_color, num)
    return cycle(mkPen(color) for color in colors)


@register_binding_controller(
    ui_name="Dynamic Graph Widget",
    klassname="DynamicGraph",
    binding_type=(NDArrayBinding, VectorNumberBinding),
    priority=-10, can_show_nothing=False)
class DisplayDynamicGraph(BaseBindingController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DynamicGraphModel, args=())

    curves = List(WeakRef(PlotDataItem))

    _pen_cycler = Instance(cycle, allow_none=False)
    _curve_cycler = Instance(cycle, allow_none=True)

    # ----------------------------------------------------------------
    # Abstract interface

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)

        self._create_curves(widget)

        widget.add_cross_target()
        widget.add_roi()
        widget.add_toolbar()
        widget.enable_export()
        widget.enable_data_toggle()

        number_action = QAction("Number of Curves", widget)
        number_action.triggered.connect(self._configure_number)
        widget.addAction(number_action)

        widget.restore(build_graph_config(self.model))

        return widget

    def destroy_widget(self):
        self._curve_cycler = None
        self.curves = []

    def value_update(self, proxy):
        y, _ = get_array_data(proxy, default=[])
        if not len(y):
            self._clear_curve_data()
            return

        # NOTE: WE cast boolean as int, as numpy method is deprecated
        if y.dtype == np.bool:
            y = y.astype(np.int)

        model = self.model
        # Generate the baseline for the x-axis
        x = generate_baseline(y, offset=model.offset, step=model.step)

        curve = next(self._curve_cycler)
        rect = get_view_range(curve)
        x, y = generate_down_sample(y, x=x, rect=rect, deviation=True)
        curve.setData(x, y)

    # ----------------------------------------------------------------
    # Private

    def _clear_curve_data(self):
        """Reset all data on the data curves of the plot item"""
        for plot in self.widget.plotItem.dataItems[:]:
            plot.setData([], [])

    def _create_curves(self, widget):
        """Clear the widget and create a new cycle and curves"""
        widget.clear()
        number = self.model.number
        self._pen_cycler = get_pen_cycler(START_COLOR, STOP_COLOR, number)
        curves = []
        for i in range(number):
            pen = next(self._pen_cycler)
            plot = widget.add_curve_item(name=f"curve-{i}", pen=pen)
            curves.append(plot)

        self.curves = curves
        self._curve_cycler = cycle(self.curves)

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _configure_number(self):
        curves, ok = QInputDialog.getInt(
            self.widget, "Number of Curves",
            f"Number (Max: {MAX_CURVES}):", self.model.number, 3, MAX_CURVES)
        if ok:
            self.model.number = curves
            self._create_curves(self.widget)
