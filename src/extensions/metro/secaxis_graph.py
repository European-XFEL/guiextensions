#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtWidgets import QAction
from traits.api import Float, Instance, WeakRef

from extensions.models.metro import MetroSecAxisGraphModel
from extensions.utils import get_array_data, get_node_value, guess_path
from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabogui.binding.api import (
    BoolBinding, FloatBinding, IntBinding, NDArrayBinding, VectorNumberBinding,
    WidgetNodeBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import AxisItem
from karabogui.graph.plots.api import KaraboPlotView

from .utils import PlotData

NUMERICAL_BINDINGS = (BoolBinding, FloatBinding, IntBinding)
VECTOR_NUMBER_BINDINGS = (NDArrayBinding, VectorNumberBinding)


class SecAxisItem(AxisItem):

    def __init__(self, orientation, showValues=True, step=1, offset=0):
        super().__init__(orientation, showValues=showValues)
        self._step = step
        self._offset = offset

    def tickStrings(self, values, scale, spacing):
        """Return the alarm names as a function of integers values

        NOTE: Always cast the value as integer due to PyQtGraph protection!
        """
        return [f'{value * self._step + self._offset:.4f}'
                .rstrip('0').rstrip('.')
                for value in values]

    def set_transform(self, step=None, offset=None):
        if step is not None:
            self._step = step
        if offset is not None:
            self._offset = offset
        self.picture = None
        self.update()


def add_secaxis(plotItem, orientation='top', step=1, offset=0):
    """"""
    old_axis = plotItem.getAxis(orientation)
    plotItem.layout.removeItem(old_axis)

    new_axis = SecAxisItem(orientation, step=step, offset=offset)
    new_axis.linkToView(plotItem.vb)
    plotItem.axes[orientation]['item'] = new_axis
    plotItem.layout.addItem(new_axis, *plotItem.axes[orientation]['pos'])
    return new_axis


@register_binding_controller(
    ui_name='Metro SecAxis Graph',
    klassname='MetroSecAxisGraph',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|Metro-SecAxisGraph'),
    priority=0, can_show_nothing=False)
class MetroSecAxisGraph(BaseBindingController):
    """The controller for the XAS graph display from a Metro output
    """
    model = Instance(MetroSecAxisGraphModel, args=())
    _plot = Instance(PlotData, args=())
    _vline = Instance(PlotData, args=())
    _offset = Float
    _secaxis = WeakRef(AxisItem)

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_legend(visible=False)
        widget.add_cross_target()
        widget.add_toolbar()
        widget.enable_data_toggle()
        widget.enable_export()
        widget.restore(build_graph_config(self.model))

        self._secaxis = add_secaxis(widget.plotItem)
        self._secaxis.setLabel(text='delay (ps)')

        # Add plot data items
        self._plot.item = widget.add_curve_item()
        self._vline.item = vline = widget.plotItem.addLine(x=self._offset)
        vline.setVisible(False)

        # Actions
        show_vertical = QAction("Show vertical line", widget)
        show_vertical.setCheckable(True)
        show_vertical.triggered.connect(vline.setVisible)
        widget.addAction(show_vertical)

        return widget

    # ----------------------------------------------------------------

    def binding_update(self, proxy):
        self._plot.path = guess_path(proxy,
                                     klass=VECTOR_NUMBER_BINDINGS,
                                     output=True)
        self._vline.path = guess_path(proxy,
                                      klass=NUMERICAL_BINDINGS)

    def value_update(self, proxy):
        self._plot_data(get_node_value(proxy, key=self._plot.path))
        offset = get_binding_value(getattr(proxy.value, self._vline.path))
        self._plot_vline(offset)

    # ----------------------------------------------------------------

    def _plot_data(self, proxy):
        x, _ = get_array_data(get_node_value(proxy, key='x'), default=[])
        y, _ = get_array_data(get_node_value(proxy, key='y0'), default=[])
        self._plot.item.setData(x, y)

    def _plot_vline(self, value):
        if value == self._offset:
            return
        self._offset = value
        self._secaxis.set_transform(step=-1/0.15,
                                    offset=value/0.15)
        self._vline.item.setValue(value)

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))
