from qtpy.QtWidgets import QGraphicsItem
from traits.api import HasStrictTraits, String, WeakRef

from karabogui.binding.api import PropertyProxy

from ..roi_graph import RectRoi


class PlotData(HasStrictTraits):
    path = String
    item = WeakRef(QGraphicsItem)


class MetroRectRoi(RectRoi):

    path = String

    def set_proxy(self, path, proxy):
        if self.path != path:
            self.path = path
            self.proxy = PropertyProxy(path=f"{proxy.path}.{path}",
                                       root_proxy=proxy.root_proxy,)
