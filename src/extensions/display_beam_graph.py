#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on October 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import numpy as np
from pyqtgraph import ROI, CrosshairROI, EllipseROI, LabelItem, Point
from qtpy.QtGui import QPainter, QPainterPath, QPainterPathStroker
from traits.api import Bool, Float, Instance, WeakRef, on_trait_change

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType, Timestamp
from karabogui.binding.api import (
    BaseBinding, ImageBinding, NodeBinding, PropertyProxy, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)
from karabogui.fonts import get_font_size_from_dpi
from karabogui.graph.common.api import KaraboLegend, float_to_string, make_pen
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)

from .display_roi_graph import BaseRoiController
from .models.api import BeamGraphModel
from .utils import get_node_value, reflect_angle, rotate_points

FONT_SIZE = get_font_size_from_dpi(8)


def roi_html(name, center=None, size=None):
    html_list = []

    # Name
    html_list.append(
        f'<span style="color: #FFF; font-size: {FONT_SIZE}pt; '
        f'font-weight: bold;">'
        f'{name or "Region of Interest"}</span>')
    # Center
    if center is not None:
        html_list.append(
            f'<span style="color: #FFF; font-size: {FONT_SIZE}pt;">'
            f'Center: ({center[0]}, {center[1]})</span>')
    # Size
    if size is not None:
        html_list.append(
            f'<span style="color: #FFF; font-size: {FONT_SIZE}pt;">'
            f'Size: ({size[0]}, {size[1]})</span>')

    html = "<br>".join(html_list)
    return f'<div style="text-align: center">{html}</div>'


# --------------------------------------------------------------------------
# Ellipse

class EllipseItem(EllipseROI):

    def _addHandles(self):
        """Override to avoid putting handles"""


class CrosshairItem(CrosshairROI):

    def __init__(self, pos=None, size=None, **kargs):
        """Reimplementing to avoid adding handles"""
        if size is None:
            size = [1, 1]
        if pos is None:
            pos = [0, 0]
        self._shape = None
        ROI.__init__(self, pos, size, **kargs)

        self.sigRegionChanged.connect(self.invalidate)
        self.aspectLocked = False

    def invalidate(self):
        self._shape = None
        self.prepareGeometryChange()

    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        if self._shape is None:
            width, height = self.getState()['size']
            p = QPainterPath()
            p.moveTo(Point(0, -height/2))
            p.lineTo(Point(0, height/2))
            p.moveTo(Point(-width/2, 0))
            p.lineTo(Point(width/2, 0))
            p = self.mapToDevice(p)
            stroker = QPainterPathStroker()
            stroker.setWidth(10)
            outline = stroker.createStroke(p)
            self._shape = self.mapFromDevice(outline)

        return self._shape

    def paint(self, p, *args):
        width, height = self.getState()['size']
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(self.currentPen)

        p.drawLine(Point(0, -height/2), Point(0, height/2))
        p.drawLine(Point(-width/2, 0), Point(width/2, 0))


class AxesLegend(KaraboLegend):

    def __init__(self):
        super(AxesLegend, self).__init__()
        self._label = LabelItem(color='w', size=f"{FONT_SIZE}pt")
        self.layout.addItem(self._label, 0, 0)
        self.layout.setContentsMargins(2, 2, 2, 2)

    def set_value(self, values):
        formatted = [float_to_string(value) for value in values]
        self._label.setText("<b>Axes</b><br>"
                            "Major: {}<br>"
                            "Minor: {}".format(*formatted))


class EllipseNode(BaseRoiController):

    crosshair_item = Instance(CrosshairROI)
    legend_item = Instance(AxesLegend, args=())
    proxy = Instance(PropertyProxy)
    angle = Float(0)

    _text_direction = (0.5, 1)  # bottom center

    def update(self):
        center = self._proxy_center
        axes = self._proxy_size
        angle = reflect_angle(self._proxy_angle)

        x, y = self._calc_position(center=center,
                                   axes=axes,
                                   angle=np.deg2rad(angle))
        self.set_ellipse((x, y))
        self.set_crosshair(center)
        self.set_size(axes)
        self.set_angle(angle)
        self.set_info(center=center, axes=axes)

    def set_ellipse(self, pos, update=True):
        # Only redraw if different
        if update and pos != self._item_position:
            # Change ROI item property
            self.roi_item.setPos(pos)

    def set_crosshair(self, pos, update=True):
        # Only redraw if different
        self.position = pos
        crosshair_pos = self.crosshair_item.pos()
        if update and pos != (crosshair_pos[0], crosshair_pos[1]):
            # Change ROI item property
            self.crosshair_item.setPos(pos)

    def set_size(self, size, update=True):
        super(EllipseNode, self).set_size(size, update=update)
        # Only redraw if different
        crosshair_size = self.crosshair_item.size()
        if update and size != (crosshair_size[0], crosshair_size[1]):
            # Change ROI item property
            self.crosshair_item.setSize(size)

    def set_angle(self, angle, update=True):
        self.angle = angle
        # Only redraw if different
        if update and angle != self.roi_item.angle():
            # Change ROI item property
            self.roi_item.setAngle(angle)
        if update and angle != self.crosshair_item.angle():
            self.crosshair_item.setAngle(angle)

    def set_info(self, center=None, axes=None):
        if self.text_item is not None and center is not None:
            center = [float_to_string(coord) for coord in center]
            self.text_item.setHtml(roi_html(self.label, center=center))
        if self.legend_item is not None and axes is not None:
            self.legend_item.set_value(axes)

    def add_to(self, plotItem):
        super(EllipseNode, self).add_to(plotItem)
        if self.crosshair_item is not None:
            plotItem.vb.addItem(self.crosshair_item, ignoreBounds=False)
        if self.legend_item is not None:
            self.legend_item.setParentItem(plotItem.vb)
            self.legend_item.anchor(itemPos=(1, 1),
                                    parentPos=(1, 1),
                                    offset=(-5, -5))

    @on_trait_change('position')
    def _update_text_position(self, pos):
        if self.text_item is not None:
            self.text_item.setPos(*pos)

    @on_trait_change('is_visible')
    def _set_visible(self, visible):
        self.crosshair_item.setVisible(visible)
        self.text_item.setVisible(visible)

    def _roi_item_default(self):
        roi = EllipseItem(pos=self._proxy_center,
                          size=self._proxy_size,
                          angle=self._proxy_angle,
                          pen=make_pen(self.color, width=2),
                          movable=False,
                          rotatable=False,
                          resizable=False,)
        roi.setVisible(self.is_visible)
        return roi

    def _crosshair_item_default(self):
        roi = CrosshairItem(pos=self._proxy_center,
                            size=self._proxy_size,
                            angle=self._proxy_angle,
                            pen=make_pen(self.color, width=2),
                            movable=False,
                            rotatable=False,
                            resizable=False,)
        roi.setVisible(self.is_visible)
        return roi

    @property
    def _proxy_center(self):
        pos = (0, 0)
        x0 = get_node_value(self.proxy, key='x0')
        y0 = get_node_value(self.proxy, key='y0')
        if x0 is not None and y0 is not None:
            x0, y0 = get_binding_value(x0), get_binding_value(y0)
            if (x0 is not None and y0 is not None
                    and np.isfinite((x0, y0)).all()):
                pos = (int(x0), int(y0))

        return pos

    @property
    def _proxy_size(self):
        size = (0, 0)
        a = get_node_value(self.proxy, key='a')
        b = get_node_value(self.proxy, key='b')
        if a is not None and b is not None:
            a, b = get_binding_value(a), get_binding_value(b)
            if (a is not None and b is not None
                    and np.isfinite((a, b)).all()):
                size = (int(a), int(b))

        return size

    @property
    def _proxy_angle(self):
        angle = 0
        theta = get_node_value(self.proxy, key='theta')
        if theta is not None:
            theta = get_binding_value(theta)
            if theta is not None and np.isfinite(theta):
                angle = theta

        return angle

    def _calc_position(self, *, center, axes, angle):
        xc, yc = center
        a, b = axes
        return rotate_points((xc - a/2, yc - b/2), center, angle)


# --------------------------------------------------------------------------

def _is_compatible(binding):
    # This controller must always have a ImageBinding for its first proxy
    return isinstance(binding, ImageBinding)


@register_binding_controller(ui_name='Beam Graph',
                             klassname='BeamGraph',
                             binding_type=BaseBinding,
                             is_compatible=_is_compatible,
                             priority=0,
                             can_show_nothing=False)
class BeamGraph(BaseBindingController):
    model = Instance(BeamGraphModel, args=())
    grayscale = Bool(True)

    # Image plots
    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())

    # Proxies
    _ellipse = Instance(BaseRoiController)

    _timestamp = Instance(Timestamp)

    def create_widget(self, parent):
        # Use a scaled-down image widget
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_colorbar()
        widget.add_toolbar()

        # Get a reference for our plotting
        self._plot = widget.plot()

        # QActions
        widget.add_axes_labels_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        return widget

    def value_update(self, proxy):
        timestamp = proxy.binding.timestamp
        if proxy is self.proxy:
            self._image_node.set_value(proxy.value)
            self._timestamp = timestamp
            if self._ellipse is None:
                self._update_image()
        elif proxy is self._ellipse.proxy and timestamp == self._timestamp:
            self._update_image()
            self._ellipse.update()

    def _update_image(self):
        if not self._image_node.is_valid:
            return

        array = self._image_node.get_data()

        # Enable/disable some widget features depending on the encoding
        self.grayscale = (self._image_node.encoding == EncodingType.GRAY
                          and array.ndim == 2)

        self._plot.setData(array)

    def add_proxy(self, proxy):
        binding = proxy.binding
        if binding is None or isinstance(binding, NodeBinding):
            if self._ellipse is None:
                self._ellipse = EllipseNode(proxy=proxy,
                                            color='g',
                                            label='Center of Mass')
                self._ellipse.add_to(self._plot)
                return True

        return False

    # ---------------------------------------------------------------------
    # Slots

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _grayscale_changed(self, grayscale):
        if grayscale:
            self.widget.add_colorbar()
            self.widget.restore({"colormap": self.model.colormap})
            self.widget.enable_aux()
        else:
            self.widget.remove_colorbar()
            self.widget.disable_aux()
