#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on May 2023
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from dataclasses import dataclass

import numpy as np
from qtpy.QtWidgets import QAction
from traits.api import Bool, Instance, WeakRef, on_trait_change

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType, Timestamp
from karabogui import icons
from karabogui.binding.api import (
    ImageBinding, PropertyProxy, VectorBoolBinding, VectorNumberBinding)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)
from karabogui.events import KaraboEvent, broadcast_event
from karabogui.graph.common.api import AspectRatio
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)

from .models.api import TickedImageGraphModel
from .utils import get_array_data


def _is_compatible(binding):
    """Only instantiate the widget with an ImageBinding"""
    return isinstance(binding, ImageBinding)


@dataclass
class Transform:
    scale: float = 1.0
    offset: float = 0.0

    @classmethod
    def from_array(cls, array):
        scale, offset = (1, 0)

        if len(array):
            offset = array[0]
            scale = np.median(np.diff(array))

        return cls(scale=scale, offset=offset)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return np.allclose((self.scale, self.offset),
                           (other.scale, other.offset))


@register_binding_controller(
    ui_name="Ticked Image Graph",
    klassname="TickedImageGraph",
    binding_type=(ImageBinding, VectorNumberBinding),
    is_compatible=_is_compatible,
    priority=-1000,
    can_show_nothing=False)
class DisplayTickedImageGraph(BaseBindingController):
    model = Instance(TickedImageGraphModel, args=())
    grayscale = Bool(True)

    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())

    _colormap_action = Instance(QAction)

    _x_proxy = Instance(PropertyProxy)
    _x_transform = Instance(Transform, args=())
    _y_proxy = Instance(PropertyProxy)
    _y_transform = Instance(Transform, args=())

    def create_widget(self, parent):
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.toolTipChanged.connect(self.show_timestamp_tooltip)
        widget.add_colorbar()
        widget.add_picker()

        # Finalize
        widget.add_toolbar()

        # Get a reference for our plotting
        self._plot = widget.plot()

        # QActions
        widget.add_axes_labels_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        # Undock - Transient model data
        if self.model.undock:
            widget.deactivate_roi()
        else:
            # Offer undock action
            undock_action = QAction(icons.undock, "Undock", widget)
            undock_action.triggered.connect(self._undock_graph)
            self._plot.vb.add_action(undock_action)

        return widget

    def binding_update(self, proxy):
        # We now add the proxies that is postponed.
        self.add_proxy(proxy)

    def add_proxy(self, proxy):
        binding = proxy.binding
        # We postpone adding the proxy if it is still None:
        # This is usual for properties of offline devices
        if binding is None:
            return True

        # Ignore the bindings that we do not want:
        # ImageBinding: already added, which is the main proxy
        # VectorBoolBinding: does not depict center values
        if isinstance(binding, (ImageBinding, VectorBoolBinding)):
            return

        # Add axes proxies
        if self._x_proxy is None:
            self._x_proxy = proxy
        elif self._y_proxy is None and proxy is not self._x_proxy:
            self._y_proxy = proxy
        else:
            # All the axes are filled. Reject additional proxies
            return False

        return True

    def value_update(self, proxy):
        if proxy is self.proxy:
            # image update
            image_data = proxy.value
            self._image_node.set_value(image_data)

            if not self._image_node.is_valid:
                return

            array = self._image_node.get_data()

            # Enable/disable some widget features depending on the encoding
            self.grayscale = (self._image_node.encoding == EncodingType.GRAY
                              and array.ndim == 2)

            self._plot.setData(array)
        elif proxy is self._x_proxy:
            array, _ = get_array_data(proxy.binding, default=[])
            transform = Transform.from_array(array)
            if transform != self._x_transform:
                self._x_transform = transform
        elif proxy is self._y_proxy:
            array, _ = get_array_data(proxy.binding, default=[])
            transform = Transform.from_array(array)
            if transform != self._y_transform:
                self._y_transform = transform

    # -----------------------------------------------------------------------
    # Trait events

    @on_trait_change('_x_transform,_y_transform')
    def _update_transform(self, _):
        x_transform, y_transform = self._x_transform, self._y_transform
        self._plot.set_transform(x_transform.scale, y_transform.scale,
                                 x_transform.offset, y_transform.offset,
                                 aspect_ratio=AspectRatio.NoAspectRatio,
                                 default=True)

        # For good measure: force rerender with transforms
        self._plot._apply_transform()

    # -----------------------------------------------------------------------
    # Qt Slots

    def show_timestamp_tooltip(self):
        image_node = self.proxy.value
        if image_node is None:
            return
        timestamp = image_node.pixels.value.data.timestamp
        if timestamp is None:
            # Can happen when we toggle aux plots
            return
        diff = Timestamp().toTimestamp() - timestamp.toTimestamp()
        self.widget.setToolTip("{} --- Last image received {:.3f} s "
                               "ago".format(self.proxy.key, diff))

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _undock_graph(self):
        """Undock the graph image but don't offer roi option"""
        model = self.model.clone_traits()
        model.undock = True
        broadcast_event(KaraboEvent.ShowUnattachedController,
                        {"model": model})

    def _grayscale_changed(self, grayscale):
        if grayscale:
            self.widget.add_colorbar()
            self.widget.restore({"colormap": self.model.colormap})
            self.widget.enable_aux()
        else:
            self.widget.remove_colorbar()
            self.widget.disable_aux()
