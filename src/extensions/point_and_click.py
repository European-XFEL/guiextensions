from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPainter, QPen
from PyQt5.QtWidgets import QWidget
from traits.api import Bytes, Instance
from numpy import exp

from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.binding.api import (
    WidgetNodeBinding, PropertyProxy, get_binding_value)
from karabogui.request import send_property_changes

from .models.simple import PointAndClickModel


class CrossesWidget(QWidget):
    """Show an image and let the user put crosses

    show the `image` (anything that can be converted to a `QImage`), together
    with `crosses`, a list of (x, y)-coordinates in the image's coordinate
    system.

    Additionally, if the widget is editable, the user can click to set own
    crosses, which will be signalled using `crossMoved`, its coordinates are in
    `edit_x` and `edit_y`, and it is shown in green.

    In red another special cross is shown, whose coordinates are in `cross_x`
    and `cross_y`. It is meant to be the last set point of the user edited
    point.

    Using the mouse wheel one may zoom into the image.
    """
    crossMoved = pyqtSignal(float, float)

    readonly = True
    image = None
    scaled = None
    crosses = ()
    cross_x = cross_y = 0
    edit_x = edit_y = 0
    offset_x = offset_y = 0
    scale_x = scale_y = 1

    def scale(self):
        self.scaled = self.image.copy(
            self.offset_x / self.scale_x, self.offset_y / self.scale_y,
            self.width() / self.scale_x, self.height() / self.scale_y
            ).scaled(self.width(), self.height())

    def paintEvent(self, event):
        if self.image is None:
            return

        if self.scaled is None or self.scaled.width() != self.width() \
                or self.scaled.height() != self.height():
            self.scale_x = self.width() / self.image.width()
            self.scale_y = self.height() / self.image.height()
            self.offset_x = self.offset_y = 0
            self.scale()

        def draw_cross(x, y, color):
            x = x * self.scale_x - self.offset_x
            y = y * self.scale_y - self.offset_y
            p.setPen(color)
            p.setRenderHint(QPainter.Antialiasing, False)
            p.drawLine(x - 30, y, x + 30, y)
            p.drawLine(x, y - 30, x, y + 30)
            p.setPen(QPen(color, 3))
            p.setRenderHint(QPainter.Antialiasing)
            p.drawEllipse(x - 20, y - 20, 40, 40)

        with QPainter(self) as p:
            p.drawImage(0, 0, self.scaled)
            for x, y in self.crosses:
                draw_cross(x, y, Qt.white)
            if not self.readonly:
                draw_cross(self.cross_x, self.cross_y, Qt.red)
                draw_cross(self.edit_x, self.edit_y, Qt.green)

    def mouseReleaseEvent(self, event):
        self.edit_x = (event.x() + self.offset_x) / self.scale_x
        self.edit_y = (event.y() + self.offset_y) / self.scale_y
        self.crossMoved.emit((event.x() + self.offset_x) / self.scale_x,
                             (event.y() + self.offset_y) / self.scale_y)
        self.update()
        event.accept()

    def wheelEvent(self, event):
        factor = exp(event.angleDelta().y() / 300)
        self.scale_x = max(factor * self.scale_x,
                           self.width() / self.image.width())
        self.scale_y = max(factor * self.scale_y,
                           self.height() / self.image.height())
        self.offset_x = min(
            max(0, (event.x() + self.offset_x) * factor - event.x()),
            self.image.width() * self.scale_x - self.width())
        self.offset_y = min(
            max(0, (event.y() + self.offset_y) * factor - event.y()),
            self.image.height() * self.scale_y - self.height())
        self.scale()
        self.update()
        event.accept()


@register_binding_controller(
    ui_name='Point-and-Click Widget',
    klassname='EditablePointAndClick',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Point-and-Click'),
    priority=0, can_show_nothing=False, can_edit=True)
class PointAndClick(BaseBindingController):
    """Show an image and let the user put crosses

    This widget is used with a special widget node type: Point-and-Click.
    In this node we expect to have two properties, `cross_x` and `cross_y`,
    which will be set to the cross chosen by the user and whose changes will
    also be shown.

    Two vectors, named `x` and `y`, contain the coordinates of additional
    crosses to be shown.
    """
    model = Instance(PointAndClickModel, args=())
    proxy_x = Instance(PropertyProxy)
    proxy_y = Instance(PropertyProxy)
    image = Bytes

    def create_widget(self, parent):
        widget = CrossesWidget(parent)
        widget.crossMoved.connect(self.cross_moved)
        return widget

    def value_update(self, proxy):
        if proxy.value is None:
            return

        self.image = get_binding_value(proxy.value.image)

        self.widget.crosses = list(zip(proxy.value.x.value,
                                       proxy.value.y.value))
        self.widget.cross_x = proxy.value.cross_x.value
        self.widget.cross_y = proxy.value.cross_y.value
        self.widget.update()

    def _image_changed(self, image):
        if image is not None:
            self.widget.image = QImage.fromData(image)
            self.widget.update()

    def set_read_only(self, readonly):
        self.widget.readonly = readonly
        self.widget.update()

    def binding_update(self, proxy):
        self.proxy_x = PropertyProxy(root_proxy=proxy.root_proxy,
                                     path=proxy.path + '.cross_x')
        self.proxy_y = PropertyProxy(root_proxy=proxy.root_proxy,
                                     path=proxy.path + '.cross_y')

    def cross_moved(self, x, y):
        if self.proxy.binding is None:
            return
        self.proxy_x.edit_value = x
        self.proxy_y.edit_value = y
        send_property_changes((self.proxy_x, self.proxy_y))
