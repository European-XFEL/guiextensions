#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################

import numpy as np
from pyqtgraph import PlotDataItem, TextItem
from qtpy.QtWidgets import QAction, QGraphicsEllipseItem, QInputDialog
from traits.api import Instance, List, WeakRef, on_trait_change

from karabogui.api import (
    BaseBindingController, KaraboPlotView, WidgetNodeBinding,
    get_binding_value, make_pen, register_binding_controller,
    with_display_type)

from .models.api import PolarPlotModel

MAX_NUM_ELLIPSES = 10


def deg_to_cart(theta, radius):
    pos_x = radius * np.cos(np.deg2rad(theta))
    pos_y = radius * np.sin(np.deg2rad(theta))
    return pos_x, pos_y


@register_binding_controller(
    ui_name='Polar Plot Widget',
    klassname='PolarPlot',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|PolarPlot'),
    priority=0, can_show_nothing=False)
class DisplayPolarPlot(BaseBindingController):
    model = Instance(PolarPlotModel, args=())
    _scatter_plot = Instance(object)
    _fit_curve = WeakRef(PlotDataItem)
    _curves = List(WeakRef(PlotDataItem))
    _text_items = List(WeakRef(TextItem))

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)

        self._scatter_plot = widget.add_scatter_item()

        number_action = QAction("Number of Ellipses", widget)
        number_action.triggered.connect(self._configure_number)
        widget.plotItem.vb.add_action(number_action)

        max_radius_action = QAction("Maximal Radius", widget)
        max_radius_action.triggered.connect(self._configure_max_radius)
        widget.plotItem.vb.add_action(max_radius_action)

        widget.plotItem.addLine(x=0, pen={'color': 'k'})
        widget.plotItem.addLine(y=0, pen={'color': 'k'})

        self._fit_curve = widget.add_curve_item(name="fit", pen=make_pen("r"))

        return widget

    def value_update(self, proxy):
        theta = self._get_value(proxy.value, "theta")
        radius = self._get_value(proxy.value, "radius")
        fit_theta = self._get_value(proxy.value, "fitTheta")
        fit_radius = self._get_value(proxy.value, "fitRadius")

        if theta is None or radius is None:
            return

        # Verify the length of both arrays
        min_size = min(len(theta), len(radius))
        theta = theta[:min_size]
        radius = radius[:min_size]

        pos_x, pos_y = deg_to_cart(theta, radius)
        r = [self.model.max_ellipses_radius] * len(theta)
        outer_ellipse_x, outer_ellipse_y = deg_to_cart(theta, r)

        if (self._scatter_plot.points() is None or
                len(pos_x) != len(self._scatter_plot.points())):
            self._plot_ellipses()

            for curve in self._curves:
                self.widget.plotItem.removeItem(curve)

            self._curves = []
            self._text_items = []
            for idx, theta in enumerate(theta):
                curve = self.widget.add_curve_item(name=f"{theta}°")
                curve.setData([0, outer_ellipse_x[idx]],
                              [0, outer_ellipse_y[idx]])
                self._curves.append(curve)

                text_item = TextItem(f"{theta}°")
                self.widget.plotItem.addItem(text_item)
                text_item.setPos(outer_ellipse_x[idx], outer_ellipse_y[idx])
                self._text_items.append(text_item)

            self._scatter_plot.clear()
            points = [{"pos": [x, y]} for x, y in zip(pos_x, pos_y)]
            self._scatter_plot.addPoints(points, symbol="s", pen=(255, 0, 0),
                                         symbolPen='w',
                                         symbolBrush=(255, 0, 0))

        else:
            self._scatter_plot.setData(pos_x, pos_y)

            for idx in range(len(self._curves)):
                x = [0, outer_ellipse_x[idx]]
                y = [0, outer_ellipse_y[idx]]
                self._curves[idx].setData(x, y)
                self._text_items[idx].setPos(outer_ellipse_x[idx],
                                             outer_ellipse_y[idx])
                self._text_items[idx].setText(f"{theta[idx]}°")

            if fit_theta is not None and fit_radius is not None:
                min_size = min(len(theta), len(radius))
                fit_theta = fit_theta[:min_size]
                fit_radius = fit_radius[:min_size]
                fit_x, fit_y = deg_to_cart(fit_theta, fit_radius)
                self._fit_curve.setData(fit_x, fit_y)

    def _get_value(self, proxy, prop):
        if hasattr(proxy, prop):
            return get_binding_value(getattr(proxy, prop))

    def _plot_ellipses(self):
        if self.widget is None:
            return

        for item in self.widget.plotItem.items[:]:
            if isinstance(item, QGraphicsEllipseItem):
                self.widget.plotItem.removeItem(item)

        pen = make_pen("k", width=0.5, alpha=150)
        for idx in range(self.model.num_ellipses):
            r = int((idx + 1) / self.model.num_ellipses *
                    self.model.max_ellipses_radius)
            circle = QGraphicsEllipseItem(-r, -r, r*2, r*2)
            circle.setPen(pen)
            self.widget.plotItem.addItem(circle)

    @on_trait_change("model.num_ellipses")
    def _num_ellipses_changed(self):
        self._plot_ellipses()

    def _configure_number(self):
        num_ellipses, ok = QInputDialog.getInt(
            self.widget, "Number of Ellipses",
            f"Number (Max: {MAX_NUM_ELLIPSES}):", self.model.num_ellipses, 1,
            MAX_NUM_ELLIPSES)
        if ok:
            self.model.num_ellipses = num_ellipses
            self._plot_ellipses()

    def _configure_max_radius(self):
        max_radius, ok = QInputDialog.getInt(
            self.widget, "Maximal radius of ellipses",
            "Number:", self.model.max_ellipses_radius, 3)
        if ok:
            self.model.max_ellipses_radius = max_radius
            self._plot_ellipses()
