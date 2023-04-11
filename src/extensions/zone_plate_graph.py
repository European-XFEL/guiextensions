#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on March 2023
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from itertools import cycle

import pyqtgraph as pg
from traits.api import Dict, Instance, List

from karabogui.binding.api import (
    ImageBinding, VectorBoolBinding, VectorNumberBinding, get_binding_value)
from karabogui.controllers.api import register_binding_controller
from karabogui.graph.common.api import AuxPlots, ImageRegion, make_pen
from karabogui.graph.image.api import ProfileAggregator

from .models.images import ZonePlateGraphModel
from .roi_graph import BaseRoiGraph, RectRoiProperty


@register_binding_controller(
    ui_name='Zone Plate Graph',
    klassname='ZonePlateGraph',
    binding_type=(ImageBinding, VectorNumberBinding),
    priority=-1000, can_show_nothing=False)
class ZonePlateGraph(BaseRoiGraph):
    model = Instance(ZonePlateGraphModel, args=())
    rois = Dict(key_trait=Instance(RectRoiProperty),
                value_trait=List(Instance(pg.InfiniteLine)))

    _colors = Instance(cycle, allow_none=False)
    _aux_plots = Instance(ProfileAggregator)

    def create_widget(self, parent):
        widget = super().create_widget(parent)

        # Setup aux plots
        controller = widget.add_aux(plot=AuxPlots.ProfilePlot, smooth=True)
        controller.current_plot = AuxPlots.ProfilePlot
        self._aux_plots = controller._aggregators[AuxPlots.ProfilePlot]

        return widget

    # -----------------------------------------------------------------------
    # Binding methods

    def add_proxy(self, proxy):
        binding = proxy.binding
        if isinstance(binding, (ImageBinding, VectorBoolBinding)):
            # Invalid input
            return

        color = next(self._colors)
        roi = RectRoiProperty(color=color,
                              label_text=self.get_label(proxy),
                              label_size=16,
                              proxy=proxy)
        roi.on_trait_change(self._set_line_visibility, 'is_visible')
        roi.on_trait_change(self._set_line_position, 'geometry')
        roi.add_to(self._plot)
        self.rois[roi] = self._add_vertical_lines(color)

        return True

    def value_update(self, proxy):
        # Update image
        if proxy is self.proxy:
            self._update_image(proxy.value)
            self._update_aux()
            return

        roi = self.get_roi(proxy)
        if roi is not None:
            self._update_roi(roi, get_binding_value(proxy))

    # -----------------------------------------------------------------------
    # Helper methods

    def get_roi(self, proxy):
        # Get the respective ROI
        for roi in self.rois:
            if proxy is roi.proxy:
                return roi

    def _add_vertical_lines(self, color):
        x_plot, y_plot = self._aux_plots.plotItems
        pen = make_pen(color)
        x0_line = x_plot.addLine(x=0, pen=pen)
        x1_line = x_plot.addLine(x=0, pen=pen)
        y0_line = y_plot.addLine(y=0, pen=pen)
        y1_line = y_plot.addLine(y=0, pen=pen)

        lines = [x0_line, x1_line, y0_line, y1_line]
        for line in lines:
            line.setVisible(False)
        return lines

    def _update_aux(self, image=None):
        # Check if image is valid
        if image is None:
            image_node = self._image_node
            if not image_node.is_valid:
                return
            image = self._image_node.get_data()

        # Update aux plots line plots
        region = ImageRegion(image, ImageRegion.Area,
                             x_slice=slice(image.shape[1]),
                             y_slice=slice(image.shape[0]))
        self._aux_plots.process(region)

    # -----------------------------------------------------------------------
    # Trait methods

    def __colors_default(self):
        return cycle(['b', 'r', 'g', 'c', 'p', 'y'])

    def _set_line_position(self, obj, name, value):
        for line, pos in zip(self.rois[obj], value):
            line.setValue(pos)

    def _set_line_visibility(self, obj, name, value):
        for line in self.rois[obj]:
            line.setVisible(value)
