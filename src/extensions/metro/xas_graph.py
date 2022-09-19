#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from traits.api import Instance

from extensions.display_xas_graph import BaseXasGraph
from extensions.models.metro import MetroXasGraphModel
from extensions.utils import get_array_data, get_node_value, guess_path
from karabogui.binding.api import (
    NDArrayBinding, VectorNumberBinding, WidgetNodeBinding)
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.graph.plots.api import (
    VectorBarGraphPlot, generate_down_sample, get_view_range)

from .utils import PlotData


@register_binding_controller(
    ui_name='Metro XAS Graph',
    klassname='MetroXasGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-XasGraph'),
    priority=0, can_show_nothing=False)
class MetroXasGraph(BaseXasGraph):
    """The controller for the XAS graph display from a Metro output
    """
    model = Instance(MetroXasGraphModel, args=())
    _std_plot = Instance(PlotData, args=())
    _intensity_plot = Instance(PlotData, args=())
    _counts_plot = Instance(PlotData, args=())

    def create_widget(self, parent):
        widget = super().create_widget(parent)
        # Adding the reference for compatibility
        self._intensity_plot.item = self.intensity_plot
        self._std_plot.item = self.std_plot
        self._counts_plot.item = self.counts_plot
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
