#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from itertools import cycle

from traits.api import DictStrAny, Instance, List, Property

from karabogui.graph.common.api import get_pen_cycler, KaraboLegend

from .base import GraphPlot
from ..const import Y_DATA


class MultiCurvePlot(GraphPlot):

    config = Property(List(DictStrAny), depends_on="_items")

    _pens = Instance(cycle, factory=get_pen_cycler, args=())
    _legend = Instance(KaraboLegend)

    def __init__(self, parent=None):
        super(MultiCurvePlot, self).__init__(parent)
        self._legend = self.widget.add_legend(visible=True)

    def add(self, config, update=True):
        """Adds the plot config in the form of:
              config = {x_data: Device, y_data: Device}
           We utilize an ItemRegistry to bookkeep all the PlotDataItems"""

        # Attach a PlotDataItem to the config
        item = self._get_item(config[Y_DATA].name)
        self._items.add(item, config)

        if update:
            self._plot_data(item, config)

    def remove(self, config):
        item = self._items.get_item_by_config(config)
        if item is not None:
            self._remove_item(item)

    def _get_item(self, name):
        """Use an unused PlotDataItem from the registry if any, we create a
           new one otherwise."""
        if self._items.has_unused():
            # The item name must be changed to the new y_data name
            # and be added back to the legend.
            item = self._items.use(name)
            self._legend.addItem(item, name)
        else:
            item = self.widget.add_curve_item(name=name,
                                              pen=next(self._pens))

        return item

    def _remove_item(self, item):
        """An item is removed by:
           1. "Hiding" it with empty data
           2. Removing it from the list in the legend.
           3. Adds to the pool of unused items.

           There are still bugs with using the PlotItem.removeItem(item) and
           is also slow, so this may be the better solution for now."""
        self._legend.removeItem(item)
        item.setData([], [])
        self._items.remove(item)

    def clear(self):
        """Deleting and recreating PlotDataItems after every scan is a bit
           expensive, so we instead store the already created items in a
           pool."""
        for item in self._items.used():
            self._remove_item(item)

    # ---------------------------------------------------------------------
    # trait handlers

    def _get_config(self):
        return list(self._items._items.values())
