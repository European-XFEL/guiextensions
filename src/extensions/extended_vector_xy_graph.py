#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on November 2021
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from itertools import cycle
from weakref import WeakValueDictionary

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QAction, QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout)
from traits.api import Instance, Int, List

from extensions.models.simple import ExtendedVectorXYGraph
from karabo.common.scenemodel.api import build_model_config
from karabogui import icons
from karabogui.binding.api import (
    VectorBoolBinding, VectorNumberBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)
from karabogui.graph.common.api import create_tool_button, get_pen_cycler
from karabogui.graph.plots.api import (
    KaraboPlotView, generate_down_sample, get_view_range)
from karabogui.util import getOpenFileName, messagebox


def _is_compatible(binding):
    """Don't allow plotting of boolean vectors"""
    return not isinstance(binding, VectorBoolBinding)


@register_binding_controller(ui_name='Extended Vector XY Graph',
                             klassname='ExtendedVectorXYGraph',
                             binding_type=VectorNumberBinding,
                             is_compatible=_is_compatible,
                             can_show_nothing=True,
                             priority=-1000)
class ExtendedVectorXYGraph(BaseBindingController):
    """The vector xy plot graph class

    - First property proxy (dragged) will declare the x axis
    - Other property proxy (added) will declare the y axis curves
    """
    model = Instance(ExtendedVectorXYGraph, args=())
    # Internal traits
    _curves = Instance(WeakValueDictionary, args=())
    _pens = Instance(cycle, allow_none=False)

    _persistent_curves = List(Instance(pg.PlotDataItem))
    _num_persistent = Int

    def create_widget(self, parent):
        widget = KaraboPlotView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_legend(visible=False)
        widget.add_cross_target()
        toolbar = widget.add_toolbar()
        widget.enable_data_toggle()
        widget.enable_export()

        # Add buttons
        # Load data
        load_button = create_tool_button(
            checkable=False,
            icon=icons.downsample,
            tooltip="Load data",
            on_clicked=self._load_persistent_data)
        try:
            toolbar.add_button(name="Load data", button=load_button)
            # GUI Changes
        except Exception:
            toolbar.add_button(button=load_button)

        # Clear data
        clear_button = create_tool_button(
            checkable=False,
            icon=icons.reset,
            tooltip="Clear loaded data",
            on_clicked=self._clear_persistent_data)
        try:
            toolbar.add_button(name="Clear data", button=clear_button)
            # GUI Changes
        except Exception:
            toolbar.add_button(button=clear_button)

        # Finalize
        widget.restore(build_model_config(self.model))

        # Actions
        legends_action = QAction("Legends", widget)
        legends_action.triggered.connect(self._configure_legends)
        widget.addAction(legends_action)

        return widget

    def __pens_default(self):
        return get_pen_cycler()

    # ----------------------------------------------------------------

    def add_proxy(self, proxy):
        curve = self.widget.add_curve_item(name=self._retrieve_legend(proxy),
                                           pen=next(self._pens))
        self._curves[proxy] = curve
        if len(self._curves) > 1:
            self.widget.set_legend(True)
        return True

    def value_update(self, proxy):
        value = get_binding_value(proxy.binding, [])
        if len(value) > 0:
            # The x-axis proxy changed!
            if proxy is self.proxy:
                for p, c in self._curves.items():
                    # since proxy is used as key for stored curves, before
                    # getting the previous values from the proxy, we have to
                    # check for Undefined
                    y_val = get_binding_value(p, [])
                    if len(value) == len(y_val):
                        rect = get_view_range(c)
                        x, y = generate_down_sample(y_val, x=value, rect=rect,
                                                    deviation=False)
                        c.setData(x, y)

                    else:
                        c.setData([], [])
            else:
                curve = self._curves.get(proxy, None)
                if curve is None:
                    # Note: This can happen on start up ...
                    return
                x_val = get_binding_value(self.proxy, [])
                if len(value) == len(x_val):
                    rect = get_view_range(curve)
                    x, y = generate_down_sample(value, x=x_val, rect=rect,
                                                deviation=False)
                    curve.setData(x, y)
                else:
                    curve.setData([], [])

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**content)

    def _configure_legends(self):
        config = {"proxies": [proxy.key for proxy in self.proxies[1:]],
                  "legends": self.model.legends}

        content, ok = LegendTableDialog.get(config, parent=self.widget)
        if ok:
            self.model.trait_set(legends=content["legends"])
            # Update legend
            for proxy, legend in zip(content["proxies"], content["legends"]):
                curve = self._retrieve_curve(proxy)
                if curve is not None:
                    curve.opts["name"] = legend
            self._refresh_plot()

    def _load_persistent_data(self):
        # Load numpy file
        filename = getOpenFileName(parent=self.widget,
                                   caption="Load saved data",
                                   filter="Numpy Binary File (*.npy *.npz)")
        if not filename:
            return

        is_npz = filename.lower().endswith("npz")
        try:
            data = np.load(filename)
        except (FileNotFoundError, ValueError):
            messagebox.show_warning(text="The supplied file cannot be opened.",
                                    title="Invalid file",
                                    parent=self.widget)
            return

        # Clear before making any changes
        self._clear_persistent_data()

        # Create persistent curves
        self._num_persistent = len(data) if is_npz else 1
        for _ in range(self._num_persistent - len(self._persistent_curves)):
            curve = self.widget.add_curve_item(pen=next(self._pens))
            self._persistent_curves.append(curve)

        # Set data
        if not is_npz:
            data = {"Data": data}
        for index, (name, array) in enumerate(data.items()):
            curve = self._persistent_curves[index]
            curve.setData(*array)
            curve.opts["name"] = f"(Loaded) {name}"

        # Add curves back to the plotItem
        self._refresh_plot(restore_persistent=False)
        for curve in self._persistent_curves[:self._num_persistent]:
            self.widget.plotItem.addItem(curve)
        self.widget.set_legend(True)

        # Finalize
        if is_npz:
            data.close()

    def _clear_persistent_data(self):
        self._refresh_plot(restore_persistent=False)

    # ----------------------------------------------------------------
    # Helpers

    def _retrieve_curve(self, prop):
        for proxy, curve in self._curves.items():
            if prop == proxy.key:
                return curve

    def _retrieve_legend(self, proxy):
        name = proxy.key
        index = (self.proxies.index(proxy) if proxy in self.proxies  # existing
                 else len(self.proxies) - 1)  # new proxy
        try:
            legend = self.model.legends[index]
            if legend:
                name = legend
        except IndexError:
            # Ignore index error and supply missing legends
            for _ in range(index + 1 - len(self.model.legends)):
                self.model.legends.append('')
        return name

    def _refresh_plot(self, restore_curves=True, restore_persistent=True):
        # Save reference before removing from plot
        curves = list(self._curves.values())
        # Remove all curves
        for curve in curves + self._persistent_curves:
            self.widget.plotItem.removeItem(curve)
        # Restore specified curves
        if restore_curves:
            for curve in curves:
                self.widget.plotItem.addItem(curve)
        if restore_persistent:
            for curve in self._persistent_curves[:self._num_persistent]:
                self.widget.plotItem.addItem(curve)


class LegendTableDialog(QDialog):
    """"""
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.setModal(False)

        # Add table
        self._table = table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(len(config["proxies"]))
        table.setHorizontalHeaderLabels(["Property", "Legend"])

        # Add entries
        zipped = zip(config["proxies"], config["legends"])
        for row, (proxy, legend) in enumerate(zipped):
            # proxy
            item = QTableWidgetItem(proxy)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            # legend
            table.setItem(row, 1, QTableWidgetItem(legend))

        # Add button boxes
        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Finalize widget
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.addWidget(table)
        layout.addWidget(button_box)
        self.setLayout(layout)

    @staticmethod
    def get(configuration, parent=None):
        dialog = LegendTableDialog(configuration, parent)
        result = dialog.exec_() == QDialog.Accepted
        content = {}
        content.update(dialog.proxies)
        content.update(dialog.legends)

        return content, result

    @property
    def proxies(self):
        return {"proxies": [self._table.item(row, 0).text()
                            for row in range(self._table.rowCount())]}

    @property
    def legends(self):
        return {"legends": [self._table.item(row, 1).text()
                            for row in range(self._table.rowCount())]}
