#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QPalette, QPen
from qtpy.QtWidgets import QGraphicsItem
from traits.api import Instance, WeakRef

from extensions.models.plots import XasGraphModel
from extensions.utils import get_array_data, get_node_value
from karabo.common.scenemodel.api import build_model_config
from karabogui.binding.api import WidgetNodeBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import AxisType, create_axis_items, make_brush
from karabogui.graph.common.const import DEFAULT_BAR_WIDTH
from karabogui.graph.image.aux_plots.base.plot import SHOWN_AXES, AuxPlotItem
from karabogui.graph.plots.api import (
    KaraboPlotView, VectorBarGraphPlot, generate_down_sample, get_view_range)

from .utils import add_twinx


def add_auxplots(widget, orientation='top', row=1, col=0, shown_axes=None):
    if shown_axes is None:
        shown_axes = SHOWN_AXES[orientation]
    axis_items = create_axis_items(AxisType.AuxPlot, shown_axes)
    aux_plotItem = AuxPlotItem(orientation=orientation,
                               axisItems=axis_items)

    graph_view = pg.GraphicsView(parent=widget)
    graph_view.setAntialiasing(False)
    graph_view.enableMouse(False)
    # Erase all transparent palettes (Performance fix: PyQtGraph == 0.11.1)
    graph_view.setPalette(QPalette())
    graph_view.setCentralItem(aux_plotItem)

    grid = widget.layout()
    grid.setRowStretch(0, 3)
    grid.setColumnStretch(0, 3)
    grid.addWidget(graph_view, row, col)
    grid.setRowStretch(row, 1)
    grid.setVerticalSpacing(10)
    return aux_plotItem


GREY_BRUSH = QBrush(QColor(192, 192, 192, 70))
NO_PEN = QPen(QColor(0, 0, 0, 0))
NO_PEN.setStyle(Qt.NoPen)


class BaseXasGraph(BaseBindingController):

    intensity_plot = WeakRef(QGraphicsItem)
    std_plot = WeakRef(QGraphicsItem)
    counts_plot = WeakRef(QGraphicsItem)

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.add_cross_target()
        widget.add_toolbar()
        widget.stateChanged.connect(self._change_model)

        # Standard deviation plot
        self.std_plot = widget.add_curve_item(connect="all")
        widget.enable_data_toggle(activate=True)

        # Intensity bar plot
        intensity_plot = VectorBarGraphPlot(width=DEFAULT_BAR_WIDTH,
                                            brush=GREY_BRUSH)
        intensity_plot.setOpts(pen=NO_PEN)
        add_twinx(widget.plotItem, data_item=intensity_plot, y_label='Io')
        self.intensity_plot = intensity_plot

        # Counts subplot
        aux_plotItem = add_auxplots(widget,
                                    shown_axes=['bottom', 'left', 'right'])
        aux_plotItem.getAxis('right').style["showValues"] = False  # no ticks
        aux_plotItem.getAxis('left').setLabel(text='counts')
        aux_viewBox = aux_plotItem.vb
        aux_viewBox.setXLink(widget.plotItem.vb)
        aux_viewBox.setBackgroundColor('w')
        counts_plot = VectorBarGraphPlot(width=DEFAULT_BAR_WIDTH,
                                         brush=make_brush('b', alpha=70))
        counts_plot.setOpts(pen=NO_PEN)
        aux_plotItem.addItem(counts_plot)
        self.counts_plot = counts_plot

        # Finalize
        widget.restore(build_model_config(self.model))
        return widget

    def value_update(self, proxy):
        if proxy.value is None:
            return

        x, _ = get_array_data(get_node_value(proxy, key='bins'),
                              default=[])

        for key, plot in self.plots.items():
            y, _ = get_array_data(get_node_value(proxy, key=key),
                                  default=[])

            # Filter out NaN values when plotting bar graphs
            if isinstance(plot, VectorBarGraphPlot):
                valid_index = np.isfinite(x)
                x = x[valid_index]
                y = y[valid_index]

            self._plot_data(plot, x=x, y=y)

    @property
    def plots(self):
        return {
            'absorption': self.std_plot,
            'intensity': self.intensity_plot,
            'counts': self.counts_plot,
        }

    def _change_model(self, content):
        self.model.trait_set(**content)

    def _plot_data(self, plot, *, x, y):
        if not len(y) or len(x) != len(y):
            plot.setData([], [])
            return

        rect = get_view_range(plot)
        x, y = generate_down_sample(y, x=x, rect=rect, deviation=True)
        if isinstance(plot, VectorBarGraphPlot):
            plot.opts['width'] = 0.8 * (x[1] - x[0])
        plot.setData(x, y)


@register_binding_controller(
    ui_name='XAS Graph',
    klassname='XasGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|XasGraph'),
    priority=0, can_show_nothing=False)
class DisplayXasGraph(BaseXasGraph):
    """
    The controller for the XAS graph display from a normal output channel
    with the following properties:

    bins : list, np.ndarray
       The (binned) x-axis values
    absorption : list, np.ndarray
       The values containing the absorption
    intensity : list, np.ndarray
       The incident intensity values
    counts : list, np.ndarray
       The values containing the counts per (binned) x-value
    """
    model = Instance(XasGraphModel, args=())
