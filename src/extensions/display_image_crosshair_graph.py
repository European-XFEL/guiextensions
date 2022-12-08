from qtpy.QtWidgets import QMessageBox, QToolButton
from traits.api import Instance, List, WeakRef

from karabogui.api import (
    BaseBindingController, ImageBinding, KaraboImageNode, KaraboImagePlot,
    KaraboImageView, MouseTool, PropertyProxy, VectorBinding,
    register_binding_controller, send_property_changes)

from .icons import crosshair_available
from .models.api import ImageCrossHairGraphModel

# Note: MouseTool is missing from `api` until 2.16.X. This is our protection
# here as the clickModes on the image item are provided then


def is_compatible(binding):
    """Only allowed for image bindings"""
    return isinstance(binding, ImageBinding)


@register_binding_controller(ui_name="Image Cross Hair Graph",
                             klassname="ImageCrossHairGraph",
                             is_compatible=is_compatible,
                             binding_type=(ImageBinding, VectorBinding),
                             priority=40, can_show_nothing=False)
class ImageCrossHairGraph(BaseBindingController):
    model = Instance(ImageCrossHairGraphModel, args=())

    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())

    # button with an icon to indicate whether crosshair is movable
    _indicator = WeakRef(QToolButton)

    _crosshairs = List(Instance(PropertyProxy))

    def create_widget(self, parent):
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        plot = widget.plot()

        # Set up click modes and connect signal
        plot.imageItem.clickTools = (MouseTool.Pointer,)
        plot.imageItem.clicked.connect(self._image_clicked)
        self._plot = plot
        widget.add_colorbar()
        widget.add_toolbar()
        indicator = QToolButton()
        indicator.setIcon(crosshair_available.icon)
        indicator.setEnabled(False)
        # Removing the border so that it doesn't look like a clickable button
        indicator.setStyleSheet("border: none;")
        widget.toolbar.add_button(indicator, separator=True)
        self._indicator = indicator

        # Colormap
        widget.add_colormap_action()
        widget.restore({"colormap": self.model.colormap})

        return widget

    def add_proxy(self, proxy):
        if proxy.root_proxy is not self.proxy.root_proxy:
            return False
        binding = proxy.binding
        if binding is None:
            # Must be a crosshair!
            self._crosshairs.append(proxy)
            self._indicator.setEnabled(True)
            return True

        if binding.display_type.split("|")[0] != "crosshair":
            return False

        if isinstance(binding, VectorBinding):
            self._crosshairs.append(proxy)
            self._indicator.setEnabled(True)
            return True
        return False

    # -----------------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**content)

    def _image_clicked(self, pos_x, pos_y):
        if len(self._crosshairs) == 1:
            text = (f"Move the Crosshair to the position ({int(pos_x)}, "
                    f"{int(pos_y)})?")
            msg_box = QMessageBox(QMessageBox.Question, "Question",
                                  text, QMessageBox.Ok | QMessageBox.Cancel,
                                  parent=self.widget)
            if msg_box.exec() == QMessageBox.Ok:
                proxy = self._crosshairs[0]
                proxy.edit_value = [pos_x, pos_y]
                send_property_changes([proxy])

    # -----------------------------------------------------------------------

    def value_update(self, proxy):
        if proxy is not self.proxy:
            return

        self._image_node.set_value(proxy.value)
        if not self._image_node.is_valid:
            return

        self._plot.setData(self._image_node.get_data())
