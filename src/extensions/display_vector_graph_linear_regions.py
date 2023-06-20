#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
from functools import partial
from weakref import WeakValueDictionary

import pyqtgraph as pg
from traits.api import Bool, Instance

from extensions.models.api import VectorGraphWithLinearRegionsModel
from karabogui.api import (
    FloatBinding, IntBinding, VectorNumberBinding, get_binding_value,
    register_binding_controller)

try:
    from karabogui.api import BaseArrayGraph
except ImportError:
    from karabogui.controllers.display.vector_graph import BaseArrayGraph

from karabogui.graph.common.api import make_brush
from karabogui.request import send_property_changes

BRUSHES = [make_brush(ch, alpha=50) for ch in "brgcpn"]


def is_compatible(binding):
    return isinstance(binding, (FloatBinding, IntBinding, VectorNumberBinding))


@register_binding_controller(
    ui_name="Vector Graph With Linear Regions",
    klassname="VectorGraphWithLinearRegions",
    binding_type=(FloatBinding, IntBinding, VectorNumberBinding),
    is_compatible=is_compatible,
    can_show_nothing=True,
    priority=-1000)
class DisplayVectorGraphWithLinearRegions(BaseArrayGraph):
    model = Instance(VectorGraphWithLinearRegionsModel, args=())
    _linear_regions = Instance(WeakValueDictionary, args=())
    _inf_lines = Instance(WeakValueDictionary, args=())
    _is_updating = Bool(False)

    def add_proxy(self, proxy):
        binding = proxy.binding
        if binding is None:
            # Add it preemptively, we add the items on `binding_update`
            return True
        if proxy in self._linear_regions or proxy in self._inf_lines:
            return False

        plot_item = None
        value = get_binding_value(binding)
        if isinstance(binding, VectorNumberBinding):
            if value is None or value.size == 2:
                brush = BRUSHES[len(self.proxies) - 1]
                plot_item = pg.LinearRegionItem([0, 0], brush=brush)
                plot_item.setZValue(-10)
                plot_item.sigRegionChangeFinished.connect(
                    partial(self._lregion_changed, proxy))
                pg.InfLineLabel(plot_item.lines[1], proxy.path, position=0.1,
                                anchor=(1, 1), color=(0, 0, 0))
                self._linear_regions[proxy] = plot_item
        elif isinstance(binding, (FloatBinding, IntBinding)):
            plot_item = pg.InfiniteLine(
                pos=0, movable=True, angle=90, label=proxy.path, labelOpts={
                    "position": 0.1, "color": (0, 0, 0),
                    "fill": (100, 100, 100, 50), "movable": True})
            plot_item.sigPositionChangeFinished.connect(
                partial(self._inf_line_changed, proxy))
            self._inf_lines[proxy] = plot_item
        if plot_item:
            self.widget.plotItem.addItem(plot_item)
            return True
        else:
            return False

    def remove_proxy(self, proxy):
        item_to_delete = None
        if proxy in self._linear_regions.keys():
            item_to_delete = self._linear_regions.pop(proxy)
        elif proxy in self._inf_lines.keys():
            item_to_delete = self._inf_lines.pop(proxy)

        if item_to_delete:
            self.widget.remove_item(item_to_delete)
            item_to_delete.deleteLater()
            return True

    def binding_update(self, proxy):
        if proxy is self.proxy:
            return
        self.add_proxy(proxy)

    def value_update(self, proxy):
        if proxy is self.proxy:
            super().value_update(proxy)
        elif proxy in self._linear_regions.keys():
            self._is_updating = True
            value = get_binding_value(proxy.binding, [0, 0])
            self._linear_regions[proxy].setRegion(value[:2])
            self._is_updating = False
        elif proxy in self._inf_lines.keys():
            self._is_updating = True
            value = get_binding_value(proxy.binding, 0)
            self._inf_lines[proxy].setValue(value)
            self._is_updating = False

    def _lregion_changed(self, proxy):
        if not self._is_updating:
            proxy.edit_value = self._linear_regions[proxy].getRegion()
            send_property_changes((proxy,))

    def _inf_line_changed(self, proxy):
        if not self._is_updating:
            proxy.edit_value = self._inf_lines[proxy].value()
            send_property_changes((proxy,))
