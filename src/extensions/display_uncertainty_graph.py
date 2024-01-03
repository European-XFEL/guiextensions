#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on June 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import weakref

import numpy as np
import pyqtgraph as pg
from qtpy.QtGui import QPainterPath, QTransform
from qtpy.QtWidgets import QGraphicsPathItem
from traits.api import Instance

from karabo.common.scenemodel.api import build_graph_config
from karabogui.binding.api import (
    BaseBinding, NodeBinding, PropertyProxy, VectorBoolBinding,
    VectorNumberBinding, get_binding_value)
from karabogui.controllers.api import register_binding_controller
from karabogui.graph.common.api import make_brush, make_pen
from karabogui.graph.plots.api import KaraboPlotView

from .display_extended_vector_xy_graph import BaseVectorXYGraph
from .models.plots import UncertaintyGraphModel
from .utils import get_array_data, get_node_value


def _is_vector_number_binding(binding):
    """Don't allow plotting of boolean vectors"""
    return (isinstance(binding, VectorNumberBinding)
            and not isinstance(binding, VectorBoolBinding))


def _is_uncertainty_band(binding):
    return (isinstance(binding, NodeBinding)
            and binding.display_type == "WidgetNode|UncertaintyBand")


class VectorFillGraphPlot(QGraphicsPathItem):
    """Creates a vector fill graph item with considering a non-zero low."""

    def __init__(self, viewbox=None, brush=None, pen=None):
        super(VectorFillGraphPlot, self).__init__()
        self._viewBox = weakref.ref(viewbox)
        if brush is not None:
            self.setBrush(brush)
        if pen is not None:
            self.setPen(pen)

        self._baseline = np.array([])
        self._low = np.array([])
        self._high = np.array([])

    @property
    def curves(self):
        size = np.min([self._baseline.size, self._low.size, self._high.size])
        if size == 0:
            return [(np.array([]), np.array([])), (np.array([]), np.array([]))]
        baseline = self._baseline[:size]
        return [(baseline, self._low[:size]), (baseline, self._high[:size])]

    def refresh(self):
        self._updatePath()
        self._viewBox().itemBoundsChanged(self)

    def setBaseline(self, baseline):
        self._baseline = np.array(baseline)
        self.refresh()

    def setRange(self, low=None, high=None):
        if low is not None:
            self._low = np.array(low)
        if high is not None:
            self._high = np.array(high)
        self.refresh()

    def _updatePath(self):
        curves = self.curves
        if curves is None:
            return

        paths = [pg.arrayToQPath(x, y) for x, y in curves]
        transform = QTransform()
        sub_path_base = paths[0].toSubpathPolygons(transform)
        sub_path_data = paths[1].toReversed().toSubpathPolygons(transform)
        sub_path_data.reverse()
        path = QPainterPath()
        for base_ele, data_ele in zip(sub_path_base, sub_path_data):
            path.addPolygon(base_ele + data_ele)
        self.setPath(path)

    def getViewBox(self):
        return self._viewBox()


@register_binding_controller(
    ui_name='Uncertainty Graph',
    klassname='UncertaintyGraph',
    binding_type=BaseBinding,
    is_compatible=_is_vector_number_binding,
    priority=0, can_show_nothing=False)
class UncertaintyGraph(BaseVectorXYGraph):
    model = Instance(UncertaintyGraphModel, args=())

    # Uncertainty elements
    _unc_proxy = Instance(PropertyProxy)
    _unc_band = Instance(QGraphicsPathItem)
    _unc_mean = Instance(pg.PlotDataItem)

    def create_widget(self, parent):
        # Setup plot
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_legend(visible=False)
        widget.add_cross_target()
        widget.add_toolbar()
        widget.enable_data_toggle()
        widget.enable_export()

        # Add a custom plot data item
        plotItem = widget.plotItem
        self._unc_mean = widget.add_curve_item(pen=make_pen('b'))
        self._unc_band = VectorFillGraphPlot(
            viewbox=plotItem.vb,
            pen=make_pen('b', alpha=60),
            brush=make_brush('b', alpha=60))
        self._unc_band.setZValue(-1000)
        plotItem.addItem(self._unc_band)
        # As we already used blue, we start with the next one.
        next(self._pens)

        # Finalize
        widget.restore(build_graph_config(self.model))
        return widget

    def binding_update(self, proxy):
        if proxy is self.proxy:
            return
        self.add_proxy(proxy)

    # ----------------------------------------------------------------

    def add_proxy(self, proxy):
        binding = proxy.binding
        if binding is None:
            # Add it preemptively, we add the items on `binding_update`
            return True
        if _is_uncertainty_band(proxy.binding):
            if self._unc_proxy is not None:
                return
            self._unc_proxy = proxy
            self._plot_uncertainty(proxy)
            curve = self._unc_mean
            self._change_name(curve, name=proxy.key)
        else:
            if proxy in self._curves:
                return
            curve = self.widget.add_curve_item(name=proxy.key,
                                               pen=next(self._pens))
        self._curves[proxy] = curve
        if len(self._curves) > 1:
            self.widget.set_legend(True)
        return True

    def value_update(self, proxy):
        if proxy is self.proxy:
            value = get_binding_value(proxy.binding, [])
            self._unc_band.setBaseline(value)
            for p, c in self._curves.items():
                if _is_uncertainty_band(p.binding):
                    p = get_node_value(p, key='mean')
                self.plot_data(x=value,
                               y=self._resolve_array(p),
                               curve=c)
        elif _is_uncertainty_band(proxy.binding):
            self._plot_uncertainty(proxy)
        else:
            curve = self._curves.get(proxy, None)
            if curve is None:
                # Note: This can happen on start up ...
                return
            self.plot_data(x=get_binding_value(self.proxy, []),
                           y=self._resolve_array(proxy),
                           curve=curve)

        # Force to paint the widget.
        self.widget.update()

    def _plot_uncertainty(self, proxy):
        mean = self._resolve_array(get_node_value(proxy, key='mean'))
        uncertainty = self._resolve_array(get_node_value(proxy,
                                                         key='uncertainty'))
        self._unc_band.setRange(low=mean - uncertainty,
                                high=mean + uncertainty)
        self.plot_data(x=get_binding_value(self.proxy, []),
                       y=mean,
                       curve=self._unc_mean)

    def _change_name(self, curve, *, name):
        curve.opts["name"] = name
        # Refresh
        plotItem = self.widget.plotItem
        plotItem.removeItem(curve)
        plotItem.addItem(curve)

    @staticmethod
    def _resolve_array(binding):
        if isinstance(binding, PropertyProxy):
            binding = binding.binding

        array, _ = get_array_data(binding, default=np.array([]))

        if array.ndim == 1:
            return array
        elif array.ndim == 2:
            return array[0]
        else:
            message = f"Doesn't support arrays with dimensions of {array.ndim}"
            raise NotImplementedError(message)
