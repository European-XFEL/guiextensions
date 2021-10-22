#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on February 20, 2020
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

import numpy as np
from pyqtgraph import InfiniteLine
from qtpy.QtWidgets import QAction
from traits.api import Instance, Undefined

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabogui.binding.api import WidgetNodeBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import make_pen
from karabogui.graph.plots.api import (
    KaraboPlotView, generate_baseline, generate_down_sample, get_view_range)

from .models.simple import DynamicDigitizerModel


@register_binding_controller(
    ui_name='Dynamic Digitizer Widget',
    klassname='DynamicDigitizer',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|DynamicDigitizer'),
    priority=-10, can_show_nothing=False)
class DisplayDynamicDigitizer(BaseBindingController):
    """The Dynamic display controller for the digitizer"""
    model = Instance(DynamicDigitizerModel, args=())
    _plot = Instance(object)
    _threshold = Instance(InfiniteLine)

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        self._plot = widget.add_curve_item()
        widget.add_cross_target()
        widget.add_roi()
        widget.add_toolbar()
        widget.enable_export()
        widget.enable_data_toggle()

        # The threshold line!
        plotItem = widget.plotItem
        line_pen = make_pen('r')
        self._threshold = InfiniteLine(pos=0, angle=0, name="threshold")
        self._threshold.setPen(line_pen)
        self._threshold.setVisible(False)
        plotItem.addItem(self._threshold)

        toggle_action = QAction("Show threshold line", widget)
        toggle_action.setCheckable(True)
        toggle_action.setChecked(False)
        toggle_action.toggled.connect(self._threshold.setVisible)
        viewbox = plotItem.vb
        viewbox.add_action(toggle_action, separator=False)

        widget.restore(build_graph_config(self.model))

        return widget

    # ----------------------------------------------------------------

    def value_update(self, proxy):
        node = proxy.value
        samples = node.samples.value
        if samples is None or samples is Undefined:
            return

        # NOTE: With empty data or only inf we clear as NaN will clear as well!
        if not len(samples) or np.isinf(samples).all():
            self._plot.setData([], [])
            return

        # Generate the baseline for the x-axis
        offset = node.offset.value
        step = node.step.value

        # Threshold might not be there!
        threshold = getattr(node, 'threshold', None)
        if threshold is not None:
            threshold_value = threshold.value
            self._threshold.setPos(threshold_value)

        x = generate_baseline(samples, offset=offset, step=step)
        rect = get_view_range(self._plot)
        x, y = generate_down_sample(samples, x=x, rect=rect, deviation=True)
        self._plot.setData(x, y)

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))
