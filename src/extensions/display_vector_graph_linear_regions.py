#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
from functools import partial
from itertools import cycle
from weakref import WeakValueDictionary

import pyqtgraph as pg
from traits.api import Bool, Constant, HasStrictTraits, Instance

from extensions.display_extended_vector_xy_graph import (
    BaseExtendedVectorXYGraph)
from extensions.models.api import (
    VectorGraphWithLinearRegionsModel, VectorXYGraphWithLinearRegionsModel)
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


class LinearRegions(HasStrictTraits):
    with_labels = Constant(True)

    _linear_regions = Instance(WeakValueDictionary, args=())
    _linear_labels = Instance(WeakValueDictionary, args=())
    _inf_lines = Instance(WeakValueDictionary, args=())
    _is_updating = Bool(False)

    _brushes = Instance(cycle, allow_none=False)

    def binding_update(self, proxy):
        if proxy is self.proxy:
            return
        self.add_proxy(proxy)

    def add_proxy(self, proxy):
        binding = proxy.binding
        if binding is None:
            # Add it preemptively, we add the items on `binding_update`
            return True

        plot_item = None
        value = get_binding_value(binding)

        # Linear regions
        is_region_proxy = (
            isinstance(binding, VectorNumberBinding)
            and proxy not in self._linear_regions
            and ((value is not None and len(value) == 2)
                 or self._in_model_as_linear_region(proxy)))
        if is_region_proxy:
            plot_item = pg.LinearRegionItem([0, 0], brush=next(self._brushes))
            plot_item.setZValue(-10)
            plot_item.sigRegionChangeFinished.connect(
                partial(self._lregion_changed, proxy))

            self._linear_regions[proxy] = plot_item
            self._linear_labels[proxy] = pg.InfLineLabel(
                plot_item.lines[1],
                self.get_label(proxy),
                position=0.1,
                anchor=(1, 1),
                color=(0, 0, 0),
                movable=True)

            # Bookkeep the linear regions in the model as we need to make
            # the distinction between these and the actual curves
            if not self._in_model_as_linear_region(proxy):
                self.model.linear_regions.append(proxy.key)

            # Hide the label if set
            visible = self.with_labels or len(self._linear_labels) > 1
            for label in self._linear_labels.values():
                label.setVisible(visible)

        # Infinite lines
        elif (isinstance(binding, (FloatBinding, IntBinding))
              and proxy not in self._inf_lines):
            plot_item = pg.InfiniteLine(
                pos=0, movable=True, angle=90, label=proxy.path, labelOpts={
                    "position": 0.1, "color": (0, 0, 0),
                    "fill": (100, 100, 100, 50), "movable": True})
            plot_item.sigPositionChangeFinished.connect(
                partial(self._inf_line_changed, proxy))
            self._inf_lines[proxy] = plot_item

        if plot_item is not None:
            self.widget.plotItem.addItem(plot_item)
            return True
        elif (not self._in_model_as_linear_region(proxy)
              and proxy not in self._curves):
            return super().add_proxy(proxy)

    def remove_proxy(self, proxy):
        item_to_delete = None
        if proxy in self._linear_regions.keys():
            item_to_delete = self._linear_regions.pop(proxy)
        elif proxy in self._inf_lines.keys():
            item_to_delete = self._inf_lines.pop(proxy)
        else:
            return super().remove_proxy(proxy)

        if item_to_delete:
            self.widget.remove_item(item_to_delete)
            item_to_delete.deleteLater()
            return True

    def value_update(self, proxy):
        if proxy in self._linear_regions.keys():
            self._is_updating = True
            value = get_binding_value(proxy.binding, [0, 0])
            self._linear_regions[proxy].setRegion(value[:2])
            self._is_updating = False
        elif proxy in self._inf_lines.keys():
            self._is_updating = True
            value = get_binding_value(proxy.binding, 0)
            self._inf_lines[proxy].setValue(value)
            self._is_updating = False
        else:
            super().value_update(proxy)

    def get_label(self, proxy):
        return proxy.path

    def _lregion_changed(self, proxy):
        if not self._is_updating:
            proxy.edit_value = self._linear_regions[proxy].getRegion()
            send_property_changes((proxy,))

    def _inf_line_changed(self, proxy):
        if not self._is_updating:
            proxy.edit_value = self._inf_lines[proxy].value()
            send_property_changes((proxy,))

    def _in_model_as_linear_region(self, proxy):
        return proxy.key in self.model.linear_regions

    def __brushes_default(self):
        return cycle(BRUSHES)


@register_binding_controller(
    ui_name="Vector Graph With Linear Regions",
    klassname="VectorGraphWithLinearRegions",
    binding_type=(FloatBinding, IntBinding, VectorNumberBinding),
    is_compatible=is_compatible,
    can_show_nothing=True,
    priority=-1000)
class DisplayVectorGraphWithLinearRegions(LinearRegions, BaseArrayGraph):
    model = Instance(VectorGraphWithLinearRegionsModel, args=())


@register_binding_controller(
    ui_name="Vector XY Graph With Linear Regions",
    klassname="VectorXYGraphWithLinearRegions",
    binding_type=(FloatBinding, IntBinding, VectorNumberBinding),
    is_compatible=is_compatible,
    can_show_nothing=True,
    priority=-2000)
class DisplayVectorXYGraphWithLinearRegions(LinearRegions,
                                            BaseExtendedVectorXYGraph):
    with_labels = Constant(False)
    model = Instance(VectorXYGraphWithLinearRegionsModel, args=())

    def add_proxy(self, proxy):
        added = super().add_proxy(proxy)
        if added:
            # Add a corresponding default legend just in case it was not added
            # (this is usually for the linear regions)
            self._retrieve_legend(proxy)

        return added

    def get_label(self, proxy):
        return self._retrieve_legend(proxy)

    def refresh_plot(self, **kwargs):
        super().refresh_plot(**kwargs)
        # Also set the legends of the linear regions
        for proxy in self._linear_regions:
            legend = self._retrieve_legend(proxy)
            self._linear_labels[proxy].setFormat(legend)
