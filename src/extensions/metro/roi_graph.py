#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on July 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from contextlib import contextmanager
from pyqtgraph import CircleROI, RectROI
from traits.api import (
    Bool, cached_property, HasStrictTraits, Instance, Int, on_trait_change,
    Property, Tuple, WeakRef)

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType
from karabogui.binding.api import (
    FloatBinding, get_binding_value, ImageBinding, IntBinding, NodeBinding,
    PropertyProxy, VectorNumberBinding, WidgetNodeBinding)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import make_pen
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)
from karabogui.request import send_property_changes

from ..models.simple import MetroCircleRoiGraphModel, MetroRectRoiGraphModel


NUMBER_BINDINGS = (IntBinding, FloatBinding)


class BaseRoiController(HasStrictTraits):

    position = Tuple(0, 0)
    size = Tuple(0, 0)

    _is_busy = Bool(False)

    def add_to(self, plotItem):
        plotItem.vb.addItem(self.roi_item, ignoreBounds=False)

    def set_visible(self, visible):
        self.roi_item.setVisible(visible)

    def set_position(self, pos, update=True, quiet=False):
        self.trait_set(position=pos, trait_change_notify=not quiet)
        # Only redraw if different
        if update and pos != self._item_position:
            self.roi_item.setPos(pos, finish=not quiet)

    def set_size(self, size, update=True, quiet=False):
        self.trait_set(size=size, trait_change_notify=not quiet)
        if update and size != self._item_size:
            self.roi_item.setSize(size, finish=not quiet)
            self.roi_item.setVisible(size != (0, 0))

    @property
    def _item_position(self):
        pos = self.roi_item.pos()
        return (pos[0], pos[1])

    @property
    def _item_size(self):
        size = self.roi_item.size()
        return (size[0], size[1])

    @contextmanager
    def busy(self):
        self._is_busy = True
        try:
            yield
        finally:
            self._is_busy = False


class CircleRoiController(BaseRoiController):

    roi_item = Instance(CircleROI)
    radius = Property(Int, depends_on="size")
    center = Property(Tuple, depends_on="position")

    def _roi_item_default(self):
        roi = CircleROI(pos=self.position,
                        radius=self.radius,
                        scaleSnap=True,
                        translateSnap=True,
                        pen=make_pen('r', width=3))
        roi.setVisible(False)
        roi.sigRegionChangeFinished.connect(self._finished_moving)
        return roi

    def _finished_moving(self):
        self.set_radius(self._item_radius, update=False)
        self.set_center(self._item_center, update=False)

    # Radius
    @property
    def _item_radius(self):
        return round(self._item_size[0] / 2)

    @cached_property
    def _get_radius(self):
        return round(self.size[0] / 2)

    def set_radius(self, radius, update=True, quiet=False):
        # Only redraw if different
        if self._is_busy or radius == self.radius:
            return

        with self.busy():
            diameter = radius * 2
            self.set_size((diameter, diameter), update=update, quiet=quiet)

    # Center
    @property
    def _item_center(self):
        x0, y0 = self._item_position
        r = self._item_radius
        return (x0+r, y0+r)

    @cached_property
    def _get_center(self):
        x0, y0 = self.position
        r = self.radius
        return (x0+r, y0+r)

    def set_center(self, center, update=True, quiet=False):
        # Only redraw if different
        if self._is_busy or tuple(center) == self.center:
            return

        with self.busy():
            xc, yc = center
            r = self.radius
            self.set_position((xc-r, yc-r), update=update, quiet=quiet)


class RectRoiController(BaseRoiController):

    roi_item = Instance(RectROI)
    geometry = Property(Tuple, depends_on="position,size")

    def _roi_item_default(self):
        x0, x1, y0, y1 = self.geometry
        roi = RectROI(pos=(x0, y0),
                      size=(x1-x0, y1-y0),
                      scaleSnap=True,
                      translateSnap=True,
                      pen=make_pen('r', width=3))
        roi.setVisible(False)
        roi.sigRegionChangeFinished.connect(self._finished_moving)
        return roi

    def _finished_moving(self):
        self.set_geometry(self._item_geometry, update=False)

    @property
    def _item_geometry(self):
        x0, y0 = self._item_position
        w, h = self._item_size
        return (x0, x0+w, y0, y0+h)

    @cached_property
    def _get_geometry(self):
        x0, y0 = int(self.position[0]), int(self.position[1])
        x1, y1 = x0 + int(self.size[0]), y0 + int(self.size[1])
        return x0, x1, y0, y1

    def set_geometry(self, geometry, update=True, quiet=False):
        # Only redraw if different
        if self._is_busy or tuple(geometry) == self.geometry:
            return

        with self.busy():
            has_geometry = bool(len(geometry))
            width, height = 0, 0
            if has_geometry:
                x0, x1, y0, y1 = geometry
                self.set_position((x0, y0), update=update, quiet=quiet)
                width, height = x1-x0, y1-y0
            self.set_size((width, height), update=update, quiet=quiet)


# --------------------------------------------------------------------------


class BaseRoiGraph(BaseBindingController):
    grayscale = Bool(True)
    roi = Instance(BaseRoiController)

    # Image plots
    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())

    _waiting = Bool(False)

    def create_widget(self, parent):
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_colorbar()

        # Finalize and add ROI afterwards
        widget.add_toolbar()

        # Get a reference for our plotting
        self._plot = widget.plot()
        self.roi.add_to(self._plot)

        # QActions
        widget.add_axes_labels_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        return widget

    def binding_update(self, proxy):
        image_path = self.model.image_path
        if not image_path or image_path not in proxy.value:
            self.model.image_path = guess_path(proxy,
                                               klass=ImageBinding,
                                               output=True)

    def value_update(self, proxy):
        self._set_image(proxy)
        self._set_roi(proxy)

    def _set_roi(self, proxy):
        pass

    # ---------------------------------------------------------------------
    # Image changes

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _set_image(self, proxy):
        # Sometimes the image_data.pixels.data.value is Undefined.
        # We catch and ignore that exception.
        try:
            node = get_node_value(proxy, self.model.image_path)
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


@register_binding_controller(
    ui_name='Metro Rect ROI Graph',
    klassname='Metro-RectRoiGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-RectRoiGraph'),
    priority=0, can_show_nothing=False)
class MetroRectRoiGraph(BaseRoiGraph):
    # Our Image Graph Model
    model = Instance(MetroRectRoiGraphModel, args=())
    roi = Instance(RectRoiController, args=())

    # Proxies
    _roi_proxy = Instance(PropertyProxy)

    # -----------------------------------------------------------------------
    # Trait events

    def binding_update(self, proxy):
        super(MetroRectRoiGraph, self).binding_update(proxy)
        path = self.model.roi_path
        if not path or path not in proxy.value:
            path = guess_path(proxy, klass=VectorNumberBinding)
            self.model.roi_path = path
        self._roi_proxy = PropertyProxy(
            root_proxy=proxy.root_proxy,
            path=f"{proxy.path}.{path}")

    @on_trait_change("roi.geometry")
    def _send_roi(self, value):
        self._roi_proxy.edit_value = value
        send_property_changes((self._roi_proxy,))
        self._waiting = True

    # -----------------------------------------------------------------------
    # Qt Slots

    def _set_roi(self, proxy):
        try:
            roi = get_binding_value(getattr(proxy.value, self.model.roi_path))
            if roi is None:
                raise AttributeError
        except AttributeError:
            self.roi.set_visible(False)
            return

        if self._waiting:
            # Check
            arrived = self.roi.geometry == tuple(roi)
            self._waiting = not arrived
            return

        self.roi.set_geometry(roi, quiet=True)


@register_binding_controller(
    ui_name='Metro Circle ROI Graph',
    klassname='Metro-CircleRoiGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-CircleRoiGraph'),
    priority=0, can_show_nothing=False)
class MetroCircleRoiGraph(BaseRoiGraph):
    # Our Image Graph Model
    model = Instance(MetroCircleRoiGraphModel, args=())
    roi = Instance(CircleRoiController, args=())

    # Proxies
    _center_proxy = Instance(PropertyProxy)
    _radius_proxy = Instance(PropertyProxy)

    def binding_update(self, proxy):
        super(MetroCircleRoiGraph, self).binding_update(proxy)
        # Center proxy
        path = self.model.center_path
        if not path or path not in proxy.value:
            path = guess_path(proxy, klass=VectorNumberBinding)
            self.model.center_path = path
        self._center_proxy = PropertyProxy(
            root_proxy=proxy.root_proxy,
            path=f"{proxy.path}.{path}")

        # Radius proxy
        path = self.model.radius_path
        if not path or path not in proxy.value:
            path = guess_path(proxy, klass=NUMBER_BINDINGS)
            self.model.radius_path = path
        self._radius_proxy = PropertyProxy(
            root_proxy=proxy.root_proxy,
            path=f"{proxy.path}.{path}")

    @on_trait_change("roi:radius")
    def _send_radius(self, value):
        self._radius_proxy.edit_value = value
        send_property_changes((self._radius_proxy,))
        self._waiting = True

    @on_trait_change("roi:center")
    def _send_center(self, value):
        self._center_proxy.edit_value = value
        send_property_changes((self._center_proxy,))
        self._waiting = True

    # -----------------------------------------------------------------------
    # Qt Slots

    def _set_roi(self, proxy):
        try:
            center = get_node_value(proxy, self.model.center_path)
            radius = get_node_value(proxy, self.model.radius_path)
            if center is None or radius is None:
                raise AttributeError
        except AttributeError:
            self.roi.set_visible(False)
            return

        if self._waiting:
            # Check
            arrived = (self.roi.radius == radius
                       and self.roi.center == tuple(center))
            self._waiting = not arrived
            return

        self.roi.set_radius(radius, quiet=True)
        self.roi.set_center(center, quiet=True)


def get_node_value(proxy, path):
    return get_binding_value(getattr(proxy.value, path))


def guess_path(proxy, *, klass, output=False):
    proxy_node = get_binding_value(proxy)
    for proxy_name in proxy_node:
        # Inspect on the top level of widget node
        binding = getattr(proxy_node, proxy_name)
        if not output and isinstance(binding, klass):
            return proxy_name

        # Inspect inside an output node
        if output and isinstance(binding, NodeBinding):
            output_node = get_binding_value(binding)
            for output_name in output_node:
                if output_name in ('path', 'trainId'):
                    continue
                binding = getattr(output_node, output_name)
                if isinstance(binding, klass):
                    return proxy_name

    return ''
