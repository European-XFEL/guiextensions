#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from contextlib import contextmanager

import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy.QtCore import Qt
from qtpy.QtGui import QPen
from qtpy.QtWidgets import QGraphicsItem
from traits.api import Array, Bool, Instance, List, WeakRef, on_trait_change

from extensions.models.plots import PeakIntegrationGraphModel
from extensions.utils import get_node_value
from karabo.common.scenemodel.api import build_model_config
from karabogui.binding.api import (
    PropertyProxy, VectorNumberBinding, WidgetNodeBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import (
    KaraboLegend, get_default_pen, make_brush, make_pen)
from karabogui.graph.plots.api import (
    KaraboPlotView, generate_down_sample, get_view_range)

NUM_PEAKS = 2
DEFAULT_REGION_SETTINGS = dict(
    movable=False,
    pen=QPen(Qt.NoPen),
    hoverPen=QPen(Qt.NoPen))
REGION_ALPHA = 80


class ColorBox(ItemSample):
    """The color box in the legend that shows the curve pen color"""

    def __init__(self, brush):
        super(ColorBox, self).__init__(item=None)
        self._brush = brush
        self._pen = QPen(Qt.NoPen)

    def paint(self, painter, *args):
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(0, 0, 10, 14)


@register_binding_controller(
    ui_name='Peak Integration Graph',
    klassname='PeakIntegrationGraph',
    binding_type=(WidgetNodeBinding, VectorNumberBinding),
    is_compatible=with_display_type('WidgetNode|PeakIntegrationGraph'),
    priority=0, can_show_nothing=False)
class DisplayPeakIntegrationGraph(BaseBindingController):
    model = Instance(PeakIntegrationGraphModel, args=())

    _curve_item = WeakRef(QGraphicsItem)
    _curve_proxy = Instance(PropertyProxy)

    _peak_regions = List(WeakRef(QGraphicsItem))
    _peak_markers = List(WeakRef(QGraphicsItem))
    _base_regions = List(WeakRef(QGraphicsItem))

    # Properties
    _peak_positions = Array()
    _peak_widths = Array()
    _peak_baseline = Array()

    # Monitor
    _peak_region_updated = Bool(default_value=False)
    _base_region_updated = Bool(default_value=False)

    # ----------------------------------------------------------------
    # Controller methods

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_cross_target()
        widget.enable_export()

        # Create peak regions
        peak_brush = make_brush('r', alpha=REGION_ALPHA)
        for _ in range(NUM_PEAKS):
            item = pg.LinearRegionItem(brush=peak_brush,
                                       **DEFAULT_REGION_SETTINGS)
            widget.plotItem.addItem(item)
            self._peak_regions.append(item)

        # Create peak markers
        peak_pen = make_pen('r', alpha=REGION_ALPHA * 2)
        for _ in range(NUM_PEAKS):
            item = pg.InfiniteLine(pen=peak_pen, movable=False)
            widget.plotItem.addItem(item)
            self._peak_markers.append(item)

        # Create base regions
        base_brush = make_brush('g', alpha=REGION_ALPHA)
        for _ in range(NUM_PEAKS):
            item = pg.LinearRegionItem(brush=base_brush,
                                       **DEFAULT_REGION_SETTINGS)
            widget.plotItem.addItem(item)
            self._base_regions.append(item)

        # Add legend
        legend = KaraboLegend()
        legend.setParentItem(widget.plotItem.vb)
        legend.anchor(itemPos=(1, 1),
                      parentPos=(1, 1),
                      offset=(-5, -5))
        legend.addItem(ColorBox(peak_brush), name='Peak region')
        legend.addItem(ColorBox(base_brush), name='Baseline')

        # Create curve item
        self._curve_item = widget.add_curve_item(pen=get_default_pen())

        # Finalize
        widget.restore(build_model_config(self.model))

        return widget

    def binding_update(self, proxy):
        self.value_update(proxy)

    def add_proxy(self, proxy):
        binding = proxy.binding
        if binding is None and self._curve_proxy is None:
            self._curve_proxy = proxy
            return True

        if not isinstance(binding, VectorNumberBinding):
            return False

        if self._curve_proxy is not None:
            return False

        self._curve_proxy = proxy
        self.value_update(proxy)

        return True

    def value_update(self, proxy):
        if get_binding_value(proxy) is None:
            return

        if proxy is self.proxy:
            # Update peak properties
            with self._monitor_peak_properties():
                peak_positions = value_from_node(proxy, key='peakPositions')
                if array_changed(self._peak_positions, peak_positions):
                    self._peak_positions = peak_positions

                peak_widths = value_from_node(proxy, key='peakWidths')
                if array_changed(self._peak_widths, peak_widths):
                    self._peak_widths = peak_widths

                peak_baseline = value_from_node(proxy, key='peakBaseline')
                if array_changed(self._peak_baseline, peak_baseline):
                    self._peak_baseline = peak_baseline

        elif proxy is self._curve_proxy:
            # Plot data
            value = get_binding_value(proxy, default=[])
            if not len(value):
                self._curve_item.setData([], [])
                return

            rect = get_view_range(self._curve_item)
            x, y = generate_down_sample(value, rect=rect, deviation=True)
            self._curve_item.setData(x, y)

    # ----------------------------------------------------------------
    # Trait changes

    @on_trait_change(['_peak_positions', '_peak_widths'])
    def _update_peak_region(self):
        self._peak_region_updated = True

    @on_trait_change(['_peak_positions', '_peak_baseline'])
    def _update_base_region(self):
        self._base_region_updated = True

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**content)

    # ----------------------------------------------------------------
    # Inner methods

    def _update_regions(self, *, regions, widths):
        for index, region in enumerate(regions):
            region.setRegion(widths + self._peak_positions[index])

    @contextmanager
    def _monitor_peak_properties(self):
        self.reset_traits(['_peak_region_updated', '_base_region_updated'])
        yield
        if self._peak_region_updated:
            self._update_regions(regions=self._peak_regions,
                                 widths=self._peak_widths)
            for index, marker in enumerate(self._peak_markers):
                marker.setValue(self._peak_positions[index])

        if self._base_region_updated:
            self._update_regions(regions=self._base_regions,
                                 widths=self._peak_baseline)


def value_from_node(proxy, *, key):
    return get_binding_value(get_node_value(proxy, key=key))


def array_changed(old, new):
    return new is not None and not np.array_equal(old, new)
