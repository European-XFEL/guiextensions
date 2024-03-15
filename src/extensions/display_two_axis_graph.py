#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
from itertools import cycle
from weakref import WeakValueDictionary

import pyqtgraph as pg
from traits.api import Instance

from extensions.models.api import XYTwoAxisGraphModel
from extensions.utils import add_twinx
from karabo.common.scenemodel.widgets.graph_utils import (
    build_graph_config, restore_graph_config)
from karabogui.api import (
    BaseBindingController, KaraboPlotView, VectorBoolBinding,
    VectorNumberBinding, generate_down_sample, get_binding_value,
    get_pen_cycler, get_view_range, register_binding_controller)


def _is_vector_number_binding(binding):
    """Don't allow plotting of boolean vectors"""
    return (isinstance(binding, VectorNumberBinding)
            and not isinstance(binding, VectorBoolBinding))


@register_binding_controller(
    ui_name="XY Two Axis Graph",
    klassname="XYTwoAxisGraph",
    binding_type=VectorNumberBinding,
    is_compatible=_is_vector_number_binding,
    can_show_nothing=True,
    priority=-100)
class DisplayXYTwoAxisGraph(BaseBindingController):

    model = Instance(XYTwoAxisGraphModel, args=())
    _curves = Instance(WeakValueDictionary, args=())
    _pens = Instance(cycle, allow_none=False)
    _second_vb = Instance(pg.ViewBox)
    _left_y_data = Instance(pg.PlotDataItem)

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_legend(visible=False)
        widget.add_roi()
        widget.add_toolbar()
        config = build_graph_config(self.model)
        widget.restore(config)

        widget.set_legend(False)
        return widget

    def add_proxy(self, proxy):
        self._add_curve(proxy)
        if len(self._curves):
            self.widget.set_legend(True)
        return True

    def _add_curve(self, proxy):
        widget = self.widget
        name = proxy.key
        legend = widget.plotItem.legend
        pen = next(self._pens)
        if self._left_y_data is None:
            curve = widget.add_curve_item(name=name, pen=pen)
            self._curves[proxy] = curve
            left_axis = widget.plotItem.getAxis("left")
            left_axis.setPen(pen)
            self._left_y_data = curve
        else:
            data_item = pg.PlotDataItem(pen=pen, name=name)
            if self._second_vb is None:
                self._second_vb = add_twinx(
                   plotItem=widget.plotItem, data_item=data_item)
            else:
                self._second_vb.addItem(data_item)
            self._curves[proxy] = data_item
            legend.addItem(data_item, name=name)

        if len(self._curves):
            widget.set_legend(True)

    def remove_proxy(self, proxy):
        plot_item = self.widget.plotItem
        item = self._curves.get(proxy)
        if item is self._left_y_data:
            self.widget.remove_item(item)
            self._left_y_data = None
        else:
            self._second_vb.removeItem(item)

        self._curves.pop(proxy)
        item.deleteLater()

        legend = plot_item.legend
        legend.removeItem(item)

        legend_visible = bool(len(self._curves))
        self.widget.set_legend(legend_visible)

        return True

    def value_update(self, proxy):
        value = get_binding_value(proxy.binding, [])

        if len(value) > 0:
            # The x-axis proxy changed!
            if proxy is self.proxy:
                for p, c in self._curves.items():
                    y_value = get_binding_value(p, [])
                    self._plot_data(c, value, y_value)
            else:
                c = self._curves.get(proxy, None)
                if c is None:
                    # Note: This can happen on start up ...
                    return

                x_value = get_binding_value(self.proxy, [])
                self._plot_data(c, x_value, value)
        else:
            # Clear the plot
            curve = self._curves.get(proxy, None)
            if curve is not None:
                curve.setData([], [])

    def __pens_default(self):
        return get_pen_cycler()

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _plot_data(self, curve, x, y):
        """Plot the data x and y on the `curve`

        Take into account a size missmatch of the data
        """
        size_x = len(x)
        size_y = len(y)
        min_size = min(size_x, size_y)
        if min_size == 0:
            curve.setData([], [])
            return

        if size_x != size_y:
            x = x[:min_size]
            y = y[:min_size]

        rect = get_view_range(curve)
        x, y = generate_down_sample(y, x=x, rect=rect, deviation=False)
        curve.setData(x, y)
