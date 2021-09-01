#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on August 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from traits.api import Bool, Instance, List, on_trait_change, String, Type

from karabogui.binding.api import (
    FloatBinding, get_binding_value, IntBinding, PropertyProxy,
    VectorNumberBinding, WidgetNodeBinding)
from karabogui.controllers.api import (
    register_binding_controller, with_display_type)
from karabogui.graph.common.api import AuxPlots, ImageRegion, make_pen
from karabogui.graph.image.api import ProfileAggregator
from karabogui.request import send_property_changes

from ..models.simple import RoiGraphModel
from ..roi_graph import BaseRoiGraph, RectRoiController
from ..utils import guess_path

NUMBER_BINDINGS = (IntBinding, FloatBinding)


class RectRoiProperty(RectRoiController):
    path = String
    proxy = Instance(PropertyProxy)
    binding_type = Type(VectorNumberBinding)
    is_waiting = Bool(False)

    def set_proxy(self, path, proxy):
        if self.path != path:
            self.path = path
            self.proxy = PropertyProxy(path=f"{proxy.path}.{path}",
                                       root_proxy=proxy.root_proxy,)

    @on_trait_change("geometry_updated")
    def _send_roi(self, value):
        self.proxy.edit_value = value
        send_property_changes((self.proxy,))
        self.is_waiting = True


@register_binding_controller(
    ui_name='Metro Zone Plate',
    klassname='Metro-ZonePlate',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-ZonePlate'),
    priority=0, can_show_nothing=False)
class MetroZonePlate(BaseRoiGraph):
    # Our Image Graph Model
    model = Instance(RoiGraphModel, args=())

    roi_n = Instance(RectRoiProperty, kw={'color': 'p', 'label': 'n'})
    roi_0 = Instance(RectRoiProperty, kw={'color': 'g', 'label': '0'})
    roi_p = Instance(RectRoiProperty, kw={'color': 'r', 'label': 'p'})

    _aux_plots = Instance(ProfileAggregator)
    _n_lines = List
    _0_lines = List
    _p_lines = List

    # -----------------------------------------------------------------------
    # Binding methods

    def create_widget(self, parent):
        widget = super(MetroZonePlate, self).create_widget(parent)
        # Setup aux plots
        controller = widget.add_aux(plot=AuxPlots.ProfilePlot, smooth=True)
        controller.current_plot = AuxPlots.ProfilePlot
        self._aux_plots = controller._aggregators[AuxPlots.ProfilePlot]

        # Draw vertical line for each x and y plots
        x_plot, y_plot = self._aux_plots.plotItems
        zipped = zip((self._n_lines, self._0_lines, self._p_lines),
                     (self.roi_n, self.roi_0, self.roi_p))
        for storage, roi in zipped:
            pen = make_pen(roi.color)
            # Add lines
            x0_line = x_plot.addLine(x=0, pen=pen)
            x1_line = x_plot.addLine(x=0, pen=pen)
            y0_line = y_plot.addLine(y=0, pen=pen)
            y1_line = y_plot.addLine(y=0, pen=pen)
            lines = [x0_line, x1_line, y0_line, y1_line]
            for line in lines:
                line.setVisible(roi.is_visible)
            storage.extend(lines)

        return widget

    def binding_update(self, proxy):
        super(MetroZonePlate, self).binding_update(proxy)
        rois = (self.roi_n, self.roi_0, self.roi_p)
        for roi in rois:
            path = guess_path(proxy,
                              klass=roi.binding_type,
                              excluded=[ex.path for ex in set(rois) - {roi}])
            roi.set_proxy(path, proxy)

    def value_update(self, proxy):
        super(MetroZonePlate, self).value_update(proxy)  # update image and ROI
        self._set_aux()

    # -----------------------------------------------------------------------
    # Trait events

    @on_trait_change('roi_n.is_visible', post_init=True)
    def _visible_n(self, visible):
        for line in self._n_lines:
            line.setVisible(visible)

    @on_trait_change('roi_0.is_visible', post_init=True)
    def _visible_0(self, visible):
        for line in self._0_lines:
            line.setVisible(visible)

    @on_trait_change('roi_p.is_visible', post_init=True)
    def _visible_p(self, visible):
        for line in self._p_lines:
            line.setVisible(visible)

    @on_trait_change('roi_n.geometry', post_init=True)
    def _geometry_n(self, geometry):
        for line, value in zip(self._n_lines, geometry):
            line.setValue(value)

    @on_trait_change('roi_0.geometry', post_init=True)
    def _geometry_0(self, geometry):
        for line, value in zip(self._0_lines, geometry):
            line.setValue(value)

    @on_trait_change('roi_p.geometry', post_init=True)
    def _geometry_p(self, geometry):
        for line, value in zip(self._p_lines, geometry):
            line.setValue(value)

    # -----------------------------------------------------------------------
    # Qt Slots

    def _set_roi(self, proxy):
        for roi in (self.roi_n, self.roi_0, self.roi_p):
            try:
                geometry = get_binding_value(getattr(proxy.value, roi.path))
            except AttributeError:
                geometry = None

            self._update_roi(roi, geometry)

    def _set_aux(self):
        # Check if image is valid
        image = self._plot.image
        if image is None:
            return

        # Update aux plots line plots
        region = ImageRegion(image, ImageRegion.Area,
                             x_slice=slice(image.shape[1]),
                             y_slice=slice(image.shape[0]))
        self._aux_plots.process(region)

    def _update_roi(self, roi, geometry=None):
        if geometry is None:
            roi.is_visible = False
            return

        if roi.is_waiting:
            # Check if property has arrived
            arrived = roi.geometry == tuple(geometry)
            roi.is_waiting = not arrived
            return

        roi.set_geometry(geometry, quiet=True)

    def _add_roi(self):
        for roi in (self.roi_n, self.roi_0, self.roi_p):
            roi.add_to(self._plot)
