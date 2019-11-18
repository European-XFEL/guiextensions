from PyQt5.QtWidgets import QWidget
from traits.api import Array, HasStrictTraits, Instance

from karabogui.graph.image.api import KaraboImageView
from karabogui.graph.plots.api import KaraboPlotView

from ..const import X_DATA, Y_DATA
from ..data.registry import ItemRegistry


class BasePlot(HasStrictTraits):

    widget = Instance(QWidget)
    current_index = Array

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


class ImagePlot(BasePlot):

    widget = Instance(KaraboImageView)

    def __init__(self, parent=None):
        super(ImagePlot, self).__init__()
        self.widget = KaraboImageView(parent)
        self.widget.add_colorbar()
        self.widget.set_colormap("viridis")


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

    def update(self, device):
        """Destroys the plot widget properly"""
        items = self._items.get_items_by_device(device)
        if not items:
            return

        for item, config in items.items():
            self._plot_data(item, config)

    def _plot_data(self, item, config):
        x_device = config[X_DATA]
        y_device = config[Y_DATA]

        # Check if they have the current index. Avoid plotting if not.
        if x_device.data.size != y_device.data.size:
            return

        item.setData(x_device.data, y_device.data)
