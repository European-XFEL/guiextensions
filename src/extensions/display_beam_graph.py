#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on October 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from pyqtgraph import ROI, CrosshairROI, EllipseROI, LabelItem, Point
from qtpy.QtGui import QPainter, QPainterPath, QPainterPathStroker
from traits.api import (
    Bool, Float, Instance, Tuple, Undefined, WeakRef, on_trait_change)

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType, Timestamp
from karabogui.binding.api import (
    FloatBinding, ImageBinding, IntBinding, WidgetNodeBinding,
    get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.fonts import get_font_size_from_dpi
from karabogui.graph.common.api import KaraboLegend, float_to_string, make_pen
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)

from .models.api import BeamGraphModel
from .roi_graph import BaseRoiController
from .utils import (
    get_node_value, reflect_angle, rotate_points, value_from_node)

FONT_SIZE = get_font_size_from_dpi(8)
NUMBER_BINDINGS = (IntBinding, FloatBinding)


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


class Legend(KaraboLegend):

    def __init__(self):
        super(Legend, self).__init__()
        self._label = LabelItem(color='w', size=f"{FONT_SIZE}pt")
        self.layout.addItem(self._label, 0, 0)
        self.layout.setContentsMargins(2, 2, 2, 2)


class AxesLegend(Legend):

    def set_values(self, values):
        formatted = [float_to_string(value if value > 1e-2 else 0)
                     for value in values]
        self._label.setText("<b>Axes</b><br>"
                            "Major: {}<br>"
                            "Minor: {}".format(*formatted))


class CenterLegend(Legend):

    def set_values(self, values):
        formatted = [float_to_string(value if value > 1e-2 else 0)
                     for value in values]
        self._label.setText("<b>Center</b><br>"
                            "x: {}<br>"
                            "y: {}".format(*formatted))


class EllipseNode(BaseRoiController):

    crosshair_item = Instance(CrosshairROI)
    center_legend = Instance(CenterLegend, args=())
    axes_legend = Instance(AxesLegend, args=())

    center = Tuple(Float(0), Float(0))
    widths = Tuple(Float(0), Float(0))
    angle = Float(0)

    _text_direction = (0.5, 1)  # bottom center

    def update(self, *, center, widths, angle):
        self.center = center = tuple(center)
        self.widths = widths = tuple(widths)
        self.angle = angle

        reflected = reflect_angle(angle)
        x, y = self._calc_position(center=center,
                                   widths=widths,
                                   angle=np.deg2rad(reflected))
        self.set_ellipse((x, y))
        self.set_crosshair(center)
        self.set_size(widths)
        self.set_angle(reflected)
        self.set_info(center=center, axes=widths)

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
        # Only redraw if different
        if update and angle != self.roi_item.angle():
            # Change ROI item property
            self.roi_item.setAngle(angle)
        if update and angle != self.crosshair_item.angle():
            self.crosshair_item.setAngle(angle)

    def set_info(self, center=None, axes=None):
        if self.center_legend is not None and center is not None:
            self.center_legend.set_values(center)
        if self.axes_legend is not None and axes is not None:
            self.axes_legend.set_values(axes)

    def add_to(self, plotItem):
        super(EllipseNode, self).add_to(plotItem)
        if self.crosshair_item is not None:
            plotItem.vb.addItem(self.crosshair_item, ignoreBounds=False)
        if self.axes_legend is not None:
            self.axes_legend.setParentItem(plotItem.vb)
            self.axes_legend.anchor(itemPos=(1, 1),
                                    parentPos=(1, 1),
                                    offset=(-5, -5))
        if self.center_legend is not None:
            self.center_legend.setParentItem(plotItem.vb)
            self.center_legend.anchor(itemPos=(0, 1),
                                      parentPos=(0, 1),
                                      offset=(5, -5))

    @on_trait_change('position')
    def _update_text_position(self, pos):
        if self.text_item is not None:
            self.text_item.setPos(*pos)

    @on_trait_change('is_visible')
    def _set_visible(self, visible):
        self.crosshair_item.setVisible(visible)
        if self.text_item is not None:
            self.text_item.setVisible(visible)

    def _roi_item_default(self):
        roi = EllipseItem(pos=self.center,
                          size=self.widths,
                          angle=self.angle,
                          pen=make_pen(self.color, width=2),
                          movable=False,
                          rotatable=False,
                          resizable=False,)
        roi.setVisible(self.is_visible)
        return roi

    def _crosshair_item_default(self):
        roi = CrosshairItem(pos=self.center,
                            size=self.widths,
                            angle=self.angle,
                            pen=make_pen(self.color, width=1),
                            movable=False,
                            rotatable=False,
                            resizable=False,)
        roi.setVisible(self.is_visible)
        return roi

    def _calc_position(self, *, center, widths, angle):
        xc, yc = center
        a, b = widths
        return rotate_points((xc - a/2, yc - b/2), center, angle)


@dataclass
class Transform:
    scale: float = 1.0
    translate: tuple = (0.0, 0.0)

    def update(self, scale, translate):
        if scale is None or translate is None:
            return False

        # Don't forget to multiply with scale
        translate = np.multiply(translate, scale)

        scale_changed = not np.isclose(scale, self.scale)
        if scale_changed:
            self.scale = scale
        translate_changed = not np.allclose(translate, self.translate)
        if translate_changed:
            self.translate = translate

        return scale_changed or translate_changed


# --------------------------------------------------------------------------

def _is_compatible(binding):
    # This controller must always have a ImageBinding for its first proxy
    return isinstance(binding, ImageBinding)


@register_binding_controller(
    ui_name='Beam Graph',
    klassname='BeamGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|BeamGraph'),
    priority=0,
    can_show_nothing=False)
class BeamGraph(BaseBindingController):
    model = Instance(BeamGraphModel, args=())
    grayscale = Bool(True)

    # Image plots
    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())

    # Proxies
    _ellipse = Instance(EllipseNode, args=())
    _transform = Instance(Transform, args=())
    _needs_update = Bool(True)

    # Transforms
    _scale = Float(1)
    _translate = Tuple(Float(0), Float(0))

    _timestamp = Instance(Timestamp)

    def create_widget(self, parent):
        # Use a scaled-down image widget
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_colorbar()
        widget.add_toolbar()

        # Get a reference for our plotting
        self._plot = widget.plot()
        self._ellipse.add_to(self._plot)

        # QActions
        widget.add_axes_labels_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        return widget

    def value_update(self, proxy):
        # Check if node binding exists
        node = get_binding_value(proxy)
        if node is None:
            return

        # Check if the data schema exists
        image_binding = get_node_value(proxy, key='image')
        if image_binding is None:
            return

        # For some reason the image dimension on first load is undefined
        image = get_binding_value(image_binding)
        if image.dims.value is Undefined:
            return

        self._update_image(image)
        self._update_transform(
            scale=value_from_node(node.transform, key='pixelScale'),
            translate=value_from_node(node.transform, key='pixelTranslate'))
        self._update_ellipse(
            center=[value_from_node(node.beamProperties, key='x0'),
                    value_from_node(node.beamProperties, key='y0')],
            widths=[value_from_node(node.beamProperties, key='a'),
                    value_from_node(node.beamProperties, key='b')],
            angle=value_from_node(node.beamProperties, key='theta'))

    def binding_update(self, proxy):
        self.value_update(proxy)

    # ---------------------------------------------------------------------
    # Helpers

    def _update_image(self, image):
        image_node = self._image_node
        image_node.set_value(image)

        if not image_node.is_valid:
            return

        array = image_node.get_data()

        # Enable/disable some widget features depending on the encoding
        self.grayscale = (image_node.encoding == EncodingType.GRAY
                          and array.ndim == 2)

        self._plot.setData(array)

    def _update_transform(self, *, scale, translate):
        if self._transform.update(scale, translate):
            scale, translate = self._transform.scale, self._transform.translate
            self._plot.set_transform(x_scale=scale, y_scale=scale,
                                     x_translate=translate[0],
                                     y_translate=translate[1],
                                     default=True)

            # For good measure: force rerender with transforms
            self._plot._apply_transform()

    def _update_ellipse(self, *, center, widths, angle):
        # Validate values
        self._ellipse.update(
            center=center if is_valid(center) else (0, 0),
            widths=widths if is_valid(widths) else (0, 0),
            angle=angle if is_valid(angle) else 0)

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


def is_valid(array):
    if not isinstance(array, Sequence):
        array = [array]
    return all([num is not None and np.isfinite(num) for num in array])
