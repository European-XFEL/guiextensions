import pyqtgraph as pg
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QGraphicsItem
from traits.api import HasStrictTraits, String, WeakRef


class PlotData(HasStrictTraits):
    path = String
    item = WeakRef(QGraphicsItem)


class TwinXViewBox(pg.ViewBox):
    """ This is a non-reactive viewbox that is used to plot a second set of
    data points in a twinx plot."""

    def __init__(self, y_label=None, parent=None):
        super().__init__(parent=parent, enableMenu=False)
        self.setMouseEnabled(y=False)
        # self.menu = None
        self.setZValue(10000)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.y_label = y_label

    def linkToPlotItem(self, plotItem):
        # Add to plot item
        plotItem.scene().addItem(self)
        viewBox = plotItem.getViewBox()
        viewBox.sigResized.connect(self._resize)

        # Link to current axes
        axis = plotItem.getAxis('right')
        axis.linkToView(self)
        self.setXLink(viewBox)

        # Show y-axis ticks and labels
        axis.style["showValues"] = True
        axis.setStyle(**axis.axisStyle)
        axis.setLabel(text=self.y_label)

    @Slot(object)
    def _resize(self, main_viewBox):
        self.setGeometry(main_viewBox.sceneBoundingRect())


def add_twinx(plotItem, data_item=None, y_label=None):
    viewBox = TwinXViewBox(y_label=y_label)
    viewBox.linkToPlotItem(plotItem)
    if data_item is not None:
        viewBox.addItem(data_item)
    return viewBox
