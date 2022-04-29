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
    QAction, QButtonGroup, QDialog, QDialogButtonBox, QHeaderView, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout)
from traits.api import Instance, List, Tuple

from extensions.models.api import ExtendedVectorXYGraph
from karabo.common.scenemodel.api import build_model_config
from karabogui import icons
from karabogui.binding.api import (
    VectorBoolBinding, VectorNumberBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)
from karabogui.graph.common.api import create_tool_button, get_pen_cycler
from karabogui.graph.plots.api import (
    KaraboPlotView, generate_down_sample, get_view_range)
from karabogui.singletons.api import get_config
from karabogui.util import getOpenFileName, messagebox

DEFAULT_LEGEND_PREFIX = "[Loaded] "
CONFLICT_LEGEND_SUFFIX = " (Conflict)"


def _is_compatible(binding):
    """Don't allow plotting of boolean vectors"""
    return not isinstance(binding, VectorBoolBinding)


@register_binding_controller(ui_name='Extended Vector XY Graph',
                             klassname='ExtendedVectorXYGraph',
                             binding_type=VectorNumberBinding,
                             is_compatible=_is_compatible,
                             can_show_nothing=True,
                             priority=-1000)
class DisplayExtendedVectorXYGraph(BaseBindingController):
    """The vector xy plot graph class

    - First property proxy (dragged) will declare the x axis
    - Other property proxy (added) will declare the y axis curves
    """
    model = Instance(ExtendedVectorXYGraph, args=())
    # Internal traits
    _curves = Instance(WeakValueDictionary, args=())
    _pens = Instance(cycle, allow_none=False)

    _persistent_curves = List(Tuple(str, Instance(pg.PlotDataItem)))

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

        # Displayed data
        edit_button = create_tool_button(
            checkable=False,
            icon=icons.edit,
            tooltip="Edit displayed data",
            on_clicked=self._configure_data)
        try:
            toolbar.add_button(name="Edit displayed data", button=edit_button)
            # GUI Changes
        except Exception:
            toolbar.add_button(button=edit_button)

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
        configure_data = QAction("Displayed Data", widget)
        configure_data.triggered.connect(self._configure_data)
        widget.addAction(configure_data)

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
                    self._plot_data(x=value,
                                    y=get_binding_value(p, []),
                                    curve=c)
            else:
                curve = self._curves.get(proxy, None)
                if curve is None:
                    # Note: This can happen on start up ...
                    return
                self._plot_data(x=get_binding_value(self.proxy, []),
                                y=value,
                                curve=curve)

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**content)

    def _configure_data(self):
        # Proxy curves
        proxy_names = [proxy.key for proxy in self.proxies[1:]]
        proxy_legends = self.model.legends
        # Persistent curves
        persistent_names, persistent_curves, persistent_legends = [], [], []
        if len(self._persistent_curves):
            persistent_names, persistent_curves = zip(*self._persistent_curves)
            persistent_legends = [curve.name() for curve in persistent_curves]

        num_proxy = len(proxy_names)
        removable = [True] * (num_proxy + len(persistent_names))
        removable[:num_proxy] = [False] * num_proxy
        config = {"names": proxy_names + list(persistent_names),
                  "legends": proxy_legends + persistent_legends,
                  "removable": removable}
        content, ok = LegendTableDialog.get(config, parent=self.widget)
        if not ok:
            return

        # Update legend
        self.model.trait_set(legends=content["legends"][:len(proxy_names)])
        zipped = zip(content["names"], content["legends"], content["removed"])
        for idx, (name, legend, removed) in enumerate(zipped):
            if removed:
                continue

            curve = None
            if name in proxy_names:
                curve = self._retrieve_curve(name)
            elif name in persistent_names:
                curve = persistent_curves[persistent_names.index(name)]
            if curve is not None:
                curve.opts["name"] = legend or name

        self._persistent_curves = [
            self._persistent_curves[idx]
            for idx, removed in enumerate(content["removed"][num_proxy:])
            if not removed
        ]
        self._refresh_plot()

    def _load_persistent_data(self):
        data_dir = ''
        if "data_dir" in get_config():
            data_dir = get_config()["data_dir"]

        # Load numpy file
        filename = getOpenFileName(parent=self.widget,
                                   caption="Load saved data",
                                   filter="Numpy Binary File (*.npy *.npz)",
                                   directory=data_dir)
        if not filename:
            return

        is_npz = filename.lower().endswith("npz")
        try:
            loaded = np.load(filename)
        except (FileNotFoundError, ValueError):
            messagebox.show_warning(text="The supplied file cannot be opened.",
                                    title="Invalid file",
                                    parent=self.widget)
            return

        try:
            # Create dictionary of data
            data = (self._select_data(loaded) if is_npz
                    else {DEFAULT_LEGEND_PREFIX + "Data": loaded})
            if data is None:
                return

            persistent_legends = [curve[1].name()
                                  for curve in self._persistent_curves]

            for index, (name, array) in enumerate(data.items()):
                while name in self.model.legends + persistent_legends:
                    name += CONFLICT_LEGEND_SUFFIX
                persistent_legends.append(name)

                curve = self.widget.add_curve_item(pen=next(self._pens))
                curve.setData(*array)
                curve.opts["name"] = name
                self._persistent_curves.append((name, curve))

            # Add curves back to the plotItem
            self._refresh_plot()
            self.widget.set_legend(True)
        finally:
            # Finalize
            if is_npz:
                loaded.close()

    def _clear_persistent_data(self):
        self._refresh_plot(restore_persistent=False)
        self._persistent_curves.clear()

    # ----------------------------------------------------------------
    # Helpers

    def _select_data(self, data):
        config = {
            "names": list(data.keys()),
            "legends": [''] * len(data),
            "removable": [True] * len(data)}
        content, ok = LegendTableDialog.get(config, parent=self.widget)
        if not ok:
            return

        zipped = zip(content["names"], content["legends"], content["removed"])
        selected = {legend or DEFAULT_LEGEND_PREFIX + name: data[name]
                    for name, legend, removed in zipped
                    if not removed}

        return selected

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
        proxy_curves = list(self._curves.values())
        persistent_curves = []
        if len(self._persistent_curves):
            _, persistent_curves = zip(*self._persistent_curves)

        # Remove all curves
        self.widget.plotItem.clearPlots()
        # Restore specified curves
        if restore_curves:
            for curve in proxy_curves:
                self.widget.plotItem.addItem(curve)
        if restore_persistent:
            for curve in persistent_curves:
                self.widget.plotItem.addItem(curve)

    @staticmethod
    def _plot_data(*, x, y, curve):
        size = min(len(x), len(y))
        if size == 0:
            curve.setData([], [])
            return

        rect = get_view_range(curve)
        curve.setData(*generate_down_sample(y[:size], x=x[:size], rect=rect,
                                            deviation=False))


class LegendTableDialog(QDialog):
    """"""
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.setModal(False)

        # Add table
        self._table = table = QTableWidget()
        table.setMinimumWidth(500)
        table.setColumnCount(3)
        table.setColumnWidth(2, 30)
        table.setRowCount(len(config["names"]))
        table.setHorizontalHeaderLabels(["Property", "Legend", ''])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        # Add button group
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(False)
        self._button_group.buttonClicked[int].connect(self._enable_row)

        # Add entries
        zipped = zip(config["names"], config["legends"], config["removable"])
        for row, (name, legend, removable) in enumerate(zipped):
            # proxy
            item = QTableWidgetItem(name)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            # legend
            line_edit = QLineEdit(legend)
            prefix = DEFAULT_LEGEND_PREFIX if removable else ''
            line_edit.setPlaceholderText(prefix + name)
            table.setCellWidget(row, 1, line_edit)
            # button
            if removable:
                button = QPushButton()
                button.setCheckable(True)
                button.setIcon(icons.delete)
                self._button_group.addButton(button, row)
                table.setCellWidget(row, 2, button)
            else:
                # Put a non-editable widget
                item = QTableWidgetItem()
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, 2, item)

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

    def _enable_row(self, row):
        button = self._button_group.button(row)
        for item in (self._table.item(row, 0), self._table.item(row, 1)):
            flags = (item.flags() ^ Qt.ItemIsEnabled if button.isChecked()
                     else item.flags() | Qt.ItemIsEnabled)
            item.setFlags(flags)

    @staticmethod
    def get(configuration, parent=None):
        dialog = LegendTableDialog(configuration, parent)
        result = dialog.exec_() == QDialog.Accepted
        content = {"names": dialog.names,
                   "legends": dialog.legends,
                   "removed": dialog.removed}
        return content, result

    @property
    def names(self):
        return [self._table.item(row, 0).text()
                for row in range(self._table.rowCount())]

    @property
    def legends(self):
        legends = []
        for row in range(self._table.rowCount()):
            legend = self._table.cellWidget(row, 1).text()
            if legend:
                while legend in legends:
                    legend += CONFLICT_LEGEND_SUFFIX
            legends.append(legend)
        return legends

    @property
    def removed(self):
        removed = [False] * self._table.rowCount()
        for button in self._button_group.buttons():
            if button.isChecked():
                index = self._button_group.id(button)
                removed[index] = True
        return removed
