#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import pyqtgraph as pg
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QColor, QPalette, QPen
from traits.api import Instance

from karabo.common.scenemodel.api import build_model_config
from karabogui.binding.api import (
    NDArrayBinding, VectorNumberBinding, WidgetNodeBinding)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import AxisType, create_axis_items, make_brush
from karabogui.graph.common.const import DEFAULT_BAR_WIDTH
from karabogui.graph.image.aux_plots.base.plot import SHOWN_AXES, AuxPlotItem
from karabogui.graph.plots.api import (
    KaraboPlotView, VectorBarGraphPlot, generate_down_sample, get_view_range)

from ..models.simple import MetroXasGraphModel
from ..utils import get_array_data, get_node_value, guess_path
from .utils import PlotData, add_twinx


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


@register_binding_controller(
    ui_name='Metro XAS Graph',
    klassname='MetroXasGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-XasGraph'),
    priority=0, can_show_nothing=False)
class MetroXasGraph(BaseBindingController):
    """The controller for the XAS graph display from a Metro output
    """
    model = Instance(MetroXasGraphModel, args=())
    _std_plot = Instance(PlotData, args=())
    _intensity_plot = Instance(PlotData, args=())
    _counts_plot = Instance(PlotData, args=())

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.add_cross_target()
        widget.add_toolbar()
        widget.stateChanged.connect(self._change_model)

        # Standard deviation plot
        self._std_plot.item = widget.add_curve_item()

        # Intensity bar plot
        intensity_plot = VectorBarGraphPlot(width=DEFAULT_BAR_WIDTH,
                                            brush=GREY_BRUSH)
        intensity_plot.opts['pen'] = NO_PEN
        add_twinx(widget.plotItem, data_item=intensity_plot, y_label='Io')
        self._intensity_plot.item = intensity_plot

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
        counts_plot.opts['pen'] = NO_PEN
        aux_plotItem.addItem(counts_plot)
        self._counts_plot.item = counts_plot

        # Finalize
        widget.restore(build_model_config(self.model))
        return widget

    def binding_update(self, proxy):
        plots = (self._std_plot, self._intensity_plot, self._counts_plot)
        for plot in plots:
            excluded = [ex.path for ex in set(plots) - {plot}]
            plot.path = guess_path(proxy,
                                   klass=(NDArrayBinding, VectorNumberBinding),
                                   excluded=excluded,
                                   output=True)

    def value_update(self, proxy):
        for plot in (self._std_plot, self._intensity_plot, self._counts_plot):
            self._plot_data(plot, proxy)

    # ----------------------------------------------------------------
    # Qt Slots

    def _plot_data(self, plot, proxy):
        if proxy.value is None:
            return
        prop = get_node_value(proxy, key=plot.path)
        x, _ = get_array_data(get_node_value(prop, key='x'), default=[])
        y, _ = get_array_data(get_node_value(prop, key='y0'), default=[])
        if not len(y) or len(x) != len(y):
            plot.item.setData([], [])
            return

        rect = get_view_range(plot.item)
        x, y = generate_down_sample(y, x=x, rect=rect, deviation=True)
        if isinstance(plot.item, VectorBarGraphPlot):
            plot.item.opts['width'] = 0.8 * (x[1] - x[0])
        plot.item.setData(x, y)

    def _change_model(self, content):
        self.model.trait_set(**content)
