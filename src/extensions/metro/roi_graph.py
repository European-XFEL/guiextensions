#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on July 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from pyqtgraph import RectROI
from traits.api import (
    Bool, Constant, HasStrictTraits, Instance, on_trait_change, Tuple,
    WeakRef)

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType
from karabogui.binding.api import (
    get_binding_value, PropertyProxy, WidgetNodeBinding)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import make_pen
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)
from karabogui.request import send_property_changes

from ..models.simple import MetroRoiGraphModel


class RoiController(HasStrictTraits):

    roi_item = Instance(RectROI)
    geometry = Tuple(0, 10, 0, 10)  # x0, x1, y0, y1

    def _roi_item_default(self):
        x0, x1, y0, y1 = self.geometry
        roi = RectROI(pos=(x0, y0),
                      size=(x1-x0, y1-y0),
                      scaleSnap=True,
                      translateSnap=True,
                      pen=make_pen('r', width=3))
        roi.setVisible(False)
        roi.sigRegionChangeFinished.connect(self._update)
        return roi

    def add_to(self, plotItem):
        plotItem.vb.addItem(self.roi_item, ignoreBounds=False)

    def set_visible(self, visible):
        self.roi_item.setVisible(visible)

    def _update(self):
        self.geometry = self._item_geometry

    def set_geometry(self, geometry):
        self.geometry = tuple(geometry)

    def _geometry_changed(self, geometry):
        # Only redraw if different
        if geometry == self._item_geometry:
            return
        has_geometry = bool(len(geometry))
        if has_geometry:
            x0, x1, y0, y1 = geometry
            self.roi_item.setPos((x0, y0), update=False)
            self.roi_item.setSize((x1-x0, y1-y0))
        self.roi_item.setVisible(has_geometry)

    @property
    def _item_geometry(self):
        pos = self.roi_item.pos()
        x0, y0 = int(pos[0]), int(pos[1])
        size = self.roi_item.size()
        x1, y1 = x0 + int(size[0]), y0 + int(size[1])
        return x0, x1, y0, y1

# --------------------------------------------------------------------------

@register_binding_controller(
    ui_name='Metro ROI Graph',
    klassname='Metro-RoiGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-RoiGraph'),
    priority=0, can_show_nothing=False)
class MetroROIGraph(BaseBindingController):
    # Our Image Graph Model
    model = Instance(MetroRoiGraphModel, args=())
    grayscale = Bool(True)

    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())
    _roi = Instance(RoiController, args=())

    # Proxies
    _image_path = Constant("preprocessing/reconstructed/raw/imag")
    _roi_path = Constant("preprocessing/roi")
    _roi_proxy = Instance(PropertyProxy)

    def create_widget(self, parent):
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_colorbar()

        # Finalize and add ROI afterwards
        widget.add_toolbar()

        # Get a reference for our plotting
        self._plot = widget.plot()
        self._roi.add_to(self._plot)

        # QActions
        widget.add_axes_labels_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        return widget

    def binding_update(self, proxy):
        self._roi_proxy = PropertyProxy(
            root_proxy=proxy.root_proxy,
            path=f"{proxy.path}.{self._roi_path}")

    def value_update(self, proxy):
        self._set_image(proxy)
        self._set_roi(proxy)

    # -----------------------------------------------------------------------
    # Trait events

    @on_trait_change("_roi:geometry")
    def _send_roi(self, value):
        self._roi_proxy.edit_value = value
        send_property_changes((self._roi_proxy,))

    # -----------------------------------------------------------------------
    # Qt Slots

    def _set_roi(self, proxy):
        try:
            roi = get_binding_value(getattr(proxy.value, self._roi_path))
            if roi is None:
                raise AttributeError
        except AttributeError:
            self._roi.set_visible(False)
            return

        self._roi.set_geometry(roi)

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _set_image(self, proxy):
        # Sometimes the image_data.pixels.data.value is Undefined.
        # We catch and ignore that exception.
        try:
            node = get_binding_value(getattr(proxy.value, self._image_path))
            image_data = get_binding_value(node.image)
            if image_data is None:
                return
            self._image_node.set_value(image_data)
        except (AttributeError, TypeError):
            return

        if not self._image_node.is_valid:
            return

        array = self._image_node.get_data()

        # Enable/disable some widget features depending on the encoding
        self.grayscale = (self._image_node.encoding == EncodingType.GRAY
                          and array.ndim == 2)

        self._plot.setData(array)

    def _grayscale_changed(self, grayscale):
        if grayscale:
            self.widget.add_colorbar()
            self.widget.restore({"colormap": self.model.colormap})
            self.widget.enable_aux()
        else:
            self.widget.remove_colorbar()
            self.widget.disable_aux()
