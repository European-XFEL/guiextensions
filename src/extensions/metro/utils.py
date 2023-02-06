from qtpy.QtWidgets import QGraphicsItem
from traits.api import HasStrictTraits, String, WeakRef

from karabogui.binding.api import PropertyProxy

from ..roi_graph import RectRoiProperty


class PlotData(HasStrictTraits):
    path = String
    item = WeakRef(QGraphicsItem)


class MetroRectRoiProperty(RectRoiProperty):

    path = String

    def set_proxy(self, path, proxy):
        if self.path != path:
            self.path = path
            self.proxy = PropertyProxy(path=f"{proxy.path}.{path}",
                                       root_proxy=proxy.root_proxy,)
