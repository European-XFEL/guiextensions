#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on July 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from contextlib import contextmanager
import pyqtgraph as pg
from traits.api import (
    Bool, cached_property, Event, HasStrictTraits, Instance,
    on_trait_change, Property, String, Tuple, WeakRef)

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType
from karabogui.binding.api import (
    FloatBinding, get_binding_value, ImageBinding, IntBinding)
from karabogui.controllers.api import (
    BaseBindingController)
from karabogui.graph.common.api import make_pen
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)
from karabogui.util import SignalBlocker

from .utils import get_node_value, guess_path


NUMBER_BINDINGS = (IntBinding, FloatBinding)


def formatted_label(text):
    html_list = []

    # Title
    html_list.append(
        f'<span style="color: #FFF; font-size: 8pt; font-weight: bold;">'
        f'{text}</span>')

    html = "<br>".join(html_list)
    return f'<div >{html}</div>'


class BaseRoiController(HasStrictTraits):

    roi_item = Instance(pg.ROI)
    text_item = Instance(pg.TextItem)

    position = Tuple(0, 0)
    size = Tuple(0, 0)

    color = String('r')
    label = String
    is_visible = Bool(False)

    _is_busy = Bool(False)
    _text_direction = (0, 1)  # lower left

    def _text_item_default(self):
        if not self.label:
            return

        item = pg.TextItem(html=formatted_label(self.label),
                           fill=(0, 0, 0, 50))
        item.setZValue(99)
        item.setVisible(self.is_visible)
        return item

    def _is_visible_changed(self, visible):
        self.roi_item.setVisible(visible)
        if self.text_item is not None:
            self.text_item.setVisible(visible)

    @on_trait_change('position,size')
    def _update_text_position(self):
        if self.text_item is None:
            return

        (x, y), (w, h) = self.position, self.size
        w, h = self._text_direction[0] * w, self._text_direction[1] * h
        self.text_item.setPos(x + w, y + h)

    def add_to(self, plotItem):
        plotItem.vb.addItem(self.roi_item, ignoreBounds=False)
        if self.text_item is not None:
            plotItem.vb.addItem(self.text_item, ignoreBounds=False)

    def set_position(self, pos, update=True):
        self.position = pos
        # Only redraw if different
        if update and pos != self._item_position:
            # Change ROI item property
            self.roi_item.setPos(pos)

    def set_size(self, size, update=True):
        self.size = size
        # Only redraw if different
        if update and size != self._item_size:
            # Change ROI item property
            self.roi_item.setSize(size)

        self.is_visible = size != (0, 0)

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

    @contextmanager
    def block_signals(self, qt_item, is_blocked=True):
        if is_blocked:
            with SignalBlocker(qt_item):
                yield
        else:
            yield


class RectRoiController(BaseRoiController):

    geometry = Property(Tuple, depends_on="position,size")
    geometry_updated = Event

    def _roi_item_default(self):
        x0, x1, y0, y1 = self.geometry
        roi = pg.RectROI(pos=(x0, y0),
                         size=(x1-x0, y1-y0),
                         scaleSnap=True,
                         translateSnap=True,
                         pen=make_pen(self.color, width=3))
        roi.setVisible(self.is_visible)
        roi.sigRegionChanged.connect(self._currently_moving)
        roi.sigRegionChangeFinished.connect(self._finished_moving)
        return roi

    def _currently_moving(self):
        self.set_geometry(self._item_geometry, update=False)

    def _finished_moving(self):
        self.geometry_updated = self.geometry

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
        has_geometry = bool(len(geometry))
        self.is_visible = has_geometry
        if tuple(geometry) == self.geometry:
            return
        if quiet and self.roi_item.isMoving:
            return

        width, height = 0, 0
        if has_geometry:
            x0, x1, y0, y1 = geometry
            with self.block_signals(self.roi_item, is_blocked=quiet):
                self.set_position((x0, y0), update=update)
            width, height = x1-x0, y1-y0
        with self.block_signals(self.roi_item, is_blocked=quiet):
            self.set_size((width, height), update=update)

# --------------------------------------------------------------------------


class BaseRoiGraph(BaseBindingController):
    grayscale = Bool(True)
    roi = Instance(BaseRoiController)

    # Image plots
    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())
    _image_path = String

    _waiting = Bool(False)

    def create_widget(self, parent):
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_colorbar()

        # Finalize and add ROI afterwards
        widget.add_toolbar()

        # Get a reference for our plotting
        self._plot = widget.plot()
        self._add_roi()

        # QActions
        widget.add_axes_labels_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        return widget

    def binding_update(self, proxy):
        if not self._image_path or self._image_path not in proxy.value:
            self._image_path = guess_path(proxy,
                                          klass=ImageBinding,
                                          output=True)

    def value_update(self, proxy):
        self._set_image(proxy)
        self._set_roi(proxy)

    def _add_roi(self):
        self.roi.add_to(self._plot)

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
            node = get_node_value(proxy, key=self._image_path)
            image_data = get_binding_value(node.value.image)
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
