#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on September 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import Slot
from qtpy.QtWidgets import (
    QAction, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGraphicsItem, QGroupBox, QVBoxLayout)
from traits.api import Instance, WeakRef

from extensions.models.metro import MetroSecAxisGraphModel
from extensions.utils import get_array_data, get_node_value, guess_path
from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabogui.binding.api import (
    BoolBinding, FloatBinding, IntBinding, NDArrayBinding, VectorNumberBinding,
    WidgetNodeBinding)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)
from karabogui.graph.common.api import AxisItem
from karabogui.graph.plots.api import KaraboPlotView, TransformDialog

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
    _vline = Instance(QGraphicsItem)
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
        self._secaxis.set_transform(step=self.model.x2_step,
                                    offset=self.model.x2_offset)

        # Actions
        trans_action = QAction("X2-Transformation", widget)
        trans_action.triggered.connect(self.configure_transformation)
        widget.addAction(trans_action)

        vline_action = QAction("Vertical Line", widget)
        vline_action.triggered.connect(self.configure_vline)
        widget.addAction(vline_action)

        # Add plot data items
        self._plot.item = widget.add_curve_item()
        self._vline = widget.plotItem.addLine(x=self.model.vline_value)
        self._vline.setVisible(self.model.vline_visible)

        return widget

    # ----------------------------------------------------------------

    def binding_update(self, proxy):
        self._plot.path = guess_path(proxy,
                                     klass=VECTOR_NUMBER_BINDINGS,
                                     output=True)

    def value_update(self, proxy):
        self._plot_data(get_node_value(proxy, key=self._plot.path))

    # ----------------------------------------------------------------

    def _plot_data(self, proxy):
        x, _ = get_array_data(get_node_value(proxy, key='x'), default=[])
        y, _ = get_array_data(get_node_value(proxy, key='y0'), default=[])
        self._plot.item.setData(x, y)

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def configure_transformation(self):
        config = build_graph_config(self.model)
        config.update({'offset': 0, 'step': 1})  # dummy
        content, ok = X2TransformDialog.get(config, parent=self.widget)
        if ok:
            self.model.trait_set(**content)
            self._secaxis.set_transform(step=content['x2_step'],
                                        offset=content['x2_offset'])

    def configure_vline(self):
        content, ok = VLineDialog.get(build_graph_config(self.model),
                                      parent=self.widget)
        if ok:
            self.model.trait_set(**content)
            self._vline.setValue(content['vline_value'])
            self._vline.setVisible(content['vline_visible'])


class X2TransformDialog(TransformDialog):

    def __init__(self, config, parent=None):
        super(X2TransformDialog, self).__init__(config, parent=parent)
        # Patch the offset precision
        self.ui_offset.setDecimals(3)
        self.ui_offset.setValue(config['x2_offset'])
        self.ui_step.setValue(config['x2_step'])

    @property
    def transformations(self):
        config = {
            "x2_offset": self.ui_offset.value(),
            "x2_step": self.ui_step.value()}

        return config

    @staticmethod
    def get(configuration, parent=None):
        dialog = X2TransformDialog(configuration, parent)
        result = dialog.exec_() == QDialog.Accepted
        content = {}
        content.update(dialog.transformations)

        return content, result


class VLineDialog(QDialog):
    """"""
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.setModal(False)

        # Add field
        self._field = QDoubleSpinBox()
        self._field.setRange(-10000, 10000)
        self._field.setDecimals(4)
        field_layout = QFormLayout()
        field_layout.addRow("Value: ", self._field)

        # Add group (checkbox)
        self._group = QGroupBox("Show vertical line")
        self._group.setCheckable(True)
        self._group.setLayout(field_layout)
        self._group.toggled.connect(self._check_state_changed)

        # Add button boxes
        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Finalize widget
        group_layout = QVBoxLayout()
        group_layout.setSpacing(15)
        group_layout.addWidget(self._group)
        group_layout.addWidget(button_box)
        self.setLayout(group_layout)

        self._field.setValue(config['vline_value'])
        self._group.setChecked(config['vline_visible'])

    @Slot(bool)
    def _check_state_changed(self, is_checked):
        self._field.setDisabled(not is_checked)

    @staticmethod
    def get(configuration, parent=None):
        dialog = VLineDialog(configuration, parent)
        result = dialog.exec_() == QDialog.Accepted
        content = {}
        content.update(dialog.vline_property)

        return content, result

    @property
    def vline_property(self):
        config = {
            "vline_value": self._field.value(),
            "vline_visible": self._group.isChecked()}

        return config
