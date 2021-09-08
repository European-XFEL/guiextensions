#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from itertools import cycle

import pyqtgraph as pg
from traits.api import Instance, List

from karabo.common.scenemodel.api import build_model_config
from karabogui.binding.api import (
    NDArrayBinding, VectorNumberBinding, WidgetNodeBinding)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import get_pen_cycler, KaraboLegend
from karabogui.graph.plots.api import (
    KaraboPlotView, VectorBarGraphPlot, generate_down_sample,
    get_view_range)

from .utils import add_twinx, PlotData
from ..models.simple import MetroTwinXGraphModel
from ..utils import get_array_data, get_node_value, guess_path


@register_binding_controller(
    ui_name='Metro TwinX Graph',
    klassname='MetroTwinXGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-TwinXGraph'),
    priority=0, can_show_nothing=False)
class MetroTwinXGraph(BaseBindingController):
    """The controller for the XAS graph display from a Metro output
    """
    model = Instance(MetroTwinXGraphModel, args=())
    _main_plot = Instance(PlotData, args=())
    _other_plots = List(Instance(PlotData))
    _legend = Instance(pg.LegendItem)
    _pens = Instance(cycle, allow_none=False)

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_cross_target()
        widget.add_toolbar()

        # Main axis
        self._main_plot.item = widget.add_curve_item(pen=next(self._pens))

        # Second y-axis
        viewBox = add_twinx(plotItem=widget.plotItem, y_label='XAS')
        for plot in self._other_plots:
            plot.item = data_item = pg.PlotDataItem(pen=next(self._pens))
            viewBox.addItem(data_item)

        # Add legend manually
        self._legend = legend = KaraboLegend(offset=(5, 5))
        legend.setBrush(None)
        legend.setParentItem(widget.plotItem.vb)

        # Finalize
        widget.restore(build_model_config(self.model))
        return widget

    def binding_update(self, proxy):
        for plot in self._plots:
            excluded = [ex.path for ex in set(self._plots) - {plot}]
            plot.path = guess_path(proxy,
                                   klass=(NDArrayBinding, VectorNumberBinding),
                                   excluded=excluded,
                                   output=True)
            # Refresh the legends
            self._legend.removeItem(plot.item)
            self._legend.addItem(plot.item, name=plot.path)

    def value_update(self, proxy):
        for plot in self._plots:
            self._plot_data(plot, proxy)

    def __pens_default(self):
        return get_pen_cycler()

    def __other_plots_default(self):
        return [PlotData() for _ in range(2)]

    # ----------------------------------------------------------------
    # Helpers

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

    @property
    def _plots(self):
        return [self._main_plot] + self._other_plots
