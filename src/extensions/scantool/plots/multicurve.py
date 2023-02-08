#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from itertools import cycle

from pyqtgraph import InfiniteLine
from traits.api import DictStrAny, Instance, List, Property

from karabogui.graph.common.api import KaraboLegend, make_pen

from ..const import Y_DATA
from .base import GraphPlot

PEN_CYCLER = cycle([make_pen('b'), make_pen('r'), make_pen('g'), make_pen('c'),
                    make_pen('p'), make_pen('n')])


class MultiCurvePlot(GraphPlot):

    config = Property(List(DictStrAny), depends_on="_items")

    _pens = Instance(cycle, factory=PEN_CYCLER, args=())
    _legend = Instance(KaraboLegend)

    def __init__(self, parent=None):
        super(MultiCurvePlot, self).__init__(parent)
        self._legend = self.widget.add_legend(visible=True)

    def add(self, config, update=True):
        """Adds the plot config in the form of:
              config = {x_data: Device, y_data: Device}
           We utilize an ItemRegistry to bookkeep all the PlotDataItems"""

        # Attach a PlotDataItem to the config.
        item = self._get_item(config[Y_DATA].device_id)
        self._items.add(item, config)

        if update:
            self._plot_data(item, config)

    def add_aligner_result(self, motor, source, positions, label):
        # To avoid overlaping lines and labels check if there is a textItem
        # with the same devices and coordinates.
        # If yes we add label to the existing label and do not a new line
        for item in self._aligner_results:
            if (item["motor"] != motor or item["source"] != source or
               not isinstance(item["plot_item"], InfiniteLine)):
                continue
            if item["plot_item"].pos().x() == positions[0]:
                label = f"{label}, {item['plot_item'].label.toPlainText()}"
                item["plot_item"].label.setText(label)
                return

        label = f"{label} ({source}/{motor})"
        line = InfiniteLine(pos=positions[0], movable=False, angle=90,
                            label=label, labelOpts={
                                "position": 0.1, "color": (0, 0, 0),
                                "fill": (100, 100, 100, 50), "movable": True})
        self.widget.plotItem.addItem(line)
        self._aligner_results.append({"motor": motor, "source": source,
                                      "plot_item": line})

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
            pen = next(self._pens)
            item = self.widget.add_curve_item(name=name,
                                              pen=pen)

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
