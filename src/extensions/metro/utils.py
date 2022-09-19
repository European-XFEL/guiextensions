from qtpy.QtWidgets import QGraphicsItem
from traits.api import HasStrictTraits, String, WeakRef


class PlotData(HasStrictTraits):
    path = String
    item = WeakRef(QGraphicsItem)
