import numpy as np
from pyqtgraph import TextItem
from qtpy.QtWidgets import QWidget
from traits.api import Array, HasStrictTraits, Instance, List

from karabogui.graph.image.api import KaraboImageView
from karabogui.graph.plots.api import KaraboPlotView

from ..const import X_DATA, Y_DATA
from ..data.registry import ItemRegistry


class BasePlot(HasStrictTraits):

    widget = Instance(QWidget)
    current_index = Array
    _aligner_results = List()

    def __init__(self):
        super(BasePlot, self).__init__()

    def add(self, config, update=True):
        """Adds the plot config that describes which device (data) are plotted
           on which axis. For instance, in 1D plots, the config tends to be:
              config = {x_data: Device, y_data: Device}
           The update flag is for showing the data in the plot, which usually
           not needed in initialization"""

    def remove(self, config):
        """Removes the plot config (and the associated item, if any)"""

    def update(self, device):
        """Updates the plot data with the updated device."""

    def clear(self):
        """Clears the plot and resets relevant properties"""

    def destroy(self):
        """Destroys the plot widget properly"""
        self.widget.setParent(None)
        self.widget.destroy()

    def add_aligner_result(self, motor, source, positions, label):
        pass

    def do_result_item_exist(self, motor, source, positions, label):
        # Check if there is a textItem with the same coordinates
        # If yes we add label to the existing label
        for item in self._aligner_results:
            if item["motor"] != motor or item["source"] != source:
                continue
            if not isinstance(item["plot_item"], TextItem):
                continue
            if (item["plot_item"].pos().x() == positions[0]
               and item["plot_item"].pos().y() == positions[1]):
                label = f"{label}, {item['plot_item'].toPlainText()}"
                item["plot_item"].setText(label)
                return True

    def remove_aligner_results(self):
        for item in self._aligner_results:
            self.widget.plotItem.removeItem(item["plot_item"])
        self._aligner_results.clear()

    def hide_aligner_results(self):
        for item in self._aligner_results:
            item["plot_item"].setVisible(False)

    def show_aligner_result(self, motor_id, source_id):
        for item in self._aligner_results:
            if motor_id is None or item["motor"] == motor_id:
                if source_id is None or item["source"] == source_id:
                    item["plot_item"].setVisible(True)


class ImagePlot(BasePlot):

    widget = Instance(KaraboImageView)

    def __init__(self, parent=None):
        super(ImagePlot, self).__init__()
        self.widget = KaraboImageView(parent)
        self.widget.add_colorbar()
        self.widget.restore(IMAGE_CONFIG)


class GraphPlot(BasePlot):

    """1D subplots are a bit tricky since they can have numerous data items
       (e.g. PlotDataItem). We keep track of the x_data and y_data of each
       plot item with ItemRegistry, which stores a dictionary of items:
           items = {PlotDataItem: config}
       where config is:
           config = {x_data: Device, y_data: Device}"""

    _items = Instance(ItemRegistry, args=())
    widget = Instance(KaraboPlotView)

    def __init__(self, parent=None):
        super(GraphPlot, self).__init__()
        self.widget = KaraboPlotView(parent)
        self.widget.enable_data_toggle(True)
        self.widget.add_toolbar()
        self.widget.enable_export()
        self.widget.restore(PLOT_CONFIG)

    def update(self, device):
        """Destroys the plot widget properly"""
        items = self._items.get_items_by_device(device)
        if not items:
            return

        for item, config in items.items():
            self._plot_data(item, config)

    def _plot_data(self, item, config):
        x_data = config[X_DATA].data
        y_data = config[Y_DATA].data

        # Mask nans
        x_data = x_data[~np.isnan(x_data)]
        y_data = y_data[~np.isnan(y_data)]

        # Check if they have the current index. Avoid plotting if not.
        if x_data.size != y_data.size:
            return

        # Check if data has only one point. Make another point to mock a "line"
        if len(x_data) == 1:
            x_data = [x_data[0]] * 2
            y_data = [y_data[0]] * 2

        item.setData(x_data, y_data)


# KaraboPlotView requires default configuration that comes from the model.
# Since the Scantool widget does not have any model traits for now, we add
# default traits for both the plot and image views
PLOT_CONFIG = {
    "x_label": "",
    "y_label": "",
    "x_units": "",
    "y_units": "",
    "x_autorange": True,
    "y_autorange": True,
    "x_grid": True,
    "y_grid": True,
    "x_log": False,
    "y_log": False,
    "x_invert": False,
    "y_invert": False,
    "x_min": 0.0,
    "x_max": 0.0,
    "y_min": 0.0,
    "y_max": 0.0}


IMAGE_CONFIG = {
    "aux_plots": 0,
    "colormap": "viridis",
    "roi_items": [],
    "roi_tool": 0,
    "x_scale": 1.0,
    "x_translate": 0.0,
    "x_label": '',
    "x_units": '',
    "y_scale": 1.0,
    "y_translate": 0.0,
    "y_label": '',
    "y_units": '',
    "show_scale": False,
    "aspect_ratio": 1
}
