#############################################################################
# Author: <cammille.carinan@xfel.eu>
# Created on January 2023
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from contextlib import contextmanager
from itertools import cycle

import pyqtgraph as pg
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QDialog, QDialogButtonBox, QHeaderView, QLineEdit, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout)
from traits.api import (
    Bool, Event, HasStrictTraits, Instance, Int, List, Property, String, Tuple,
    Type, WeakRef, cached_property, on_trait_change)

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.native import EncodingType
from karabogui import icons
from karabogui.binding.api import (
    FloatBinding, ImageBinding, IntBinding, PropertyProxy, VectorBoolBinding,
    VectorNumberBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)
from karabogui.graph.common.api import create_tool_button, make_pen
from karabogui.graph.image.api import (
    KaraboImageNode, KaraboImagePlot, KaraboImageView)
from karabogui.request import send_property_changes
from karabogui.util import SignalBlocker

from .models.api import RectRoiGraphModel

NUMBER_BINDINGS = (IntBinding, FloatBinding)


def formatted_label(text, size=8):
    html_list = []

    # Title
    html_list.append(
        f'<span style="color: #FFF; font-size: {size}pt; font-weight: bold;">'
        f'{text}</span>')

    html = "<br>".join(html_list)
    return f'<div >{html}</div>'


class BaseRoiController(HasStrictTraits):

    roi_item = Instance(pg.ROI)
    text_item = Instance(pg.TextItem)

    position = Tuple(0, 0)
    size = Tuple(0, 0)

    color = String('r')
    label_text = String
    label_size = Int(8)
    is_visible = Bool(False)

    _is_busy = Bool(False)
    _text_direction = (0, 1)  # lower left

    def _text_item_default(self):
        if not self.label_text:
            return

        item = pg.TextItem(
            html=formatted_label(self.label_text, size=self.label_size),
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

    @on_trait_change('label_text,label_size')
    def _set_label(self):
        self.text_item.setHtml(formatted_label(self.label_text,
                                               size=self.label_size))

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


class RectRoiProperty(RectRoiController):
    """A Rect ROI controller with an attached Karabo `PropertyProxy`"""

    proxy = Instance(PropertyProxy)
    binding_type = Type(VectorNumberBinding)
    is_waiting = Bool(False)

    @on_trait_change("geometry_updated")
    def _send_roi(self, value):
        self.proxy.edit_value = value
        send_property_changes((self.proxy,))
        self.is_waiting = True


class BaseRoiGraph(BaseBindingController):
    grayscale = Bool(True)

    # Image plots
    _plot = WeakRef(KaraboImagePlot)
    _image_node = Instance(KaraboImageNode, args=())
    _image_path = String

    _waiting = Bool(False)
    _edit_button = WeakRef(QToolButton)
    _colors = Instance(cycle, allow_none=False)

    rois = List(Instance(RectRoiProperty))

    def create_widget(self, parent):
        widget = KaraboImageView(parent=parent)
        widget.stateChanged.connect(self._change_model)
        widget.add_colorbar()

        # Finalize and add ROI afterwards
        toolbar = widget.add_toolbar()
        # Displayed data
        self._edit_button = edit_button = create_tool_button(
            checkable=False,
            icon=icons.edit,
            tooltip="Edit ROI labels",
            on_clicked=self._edit_labels)
        try:
            toolbar.add_button(name=edit_button.toolTip(),
                               button=edit_button)
        except TypeError:
            # The toolbar from the GUI has been changed.
            toolbar.add_button(button=edit_button)

        # Get a reference for our plotting
        self._plot = widget.plot()

        # QActions
        widget.add_axes_labels_dialog()
        widget.add_transforms_dialog()

        # Restore the model information
        widget.restore(build_graph_config(self.model))

        return widget

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

    # ---------------------------------------------------------------------
    # Image changes

    def _change_model(self, content):
        self.model.trait_set(**restore_graph_config(content))

    def _update_image(self, image=None):
        image_node = self._image_node
        if image is not None:
            image_node.set_value(image)

        if not image_node.is_valid:
            return

        array = image_node.get_data()

        # Enable/disable some widget features depending on the encoding
        self.grayscale = (image_node.encoding == EncodingType.GRAY
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

    # -----------------------------------------------------------------------
    # Helper methods

    def get_roi(self, proxy):
        # Get the respective ROI
        for roi in self.rois:
            if proxy is roi.proxy:
                return roi

    def get_label(self, proxy):
        name = proxy.path
        roi_proxies = self.proxies[1:]
        index = (roi_proxies.index(proxy) if proxy in roi_proxies  # existing
                 else len(roi_proxies))  # new proxy
        labels = self.model.labels
        try:
            label = labels[index]
            if label:
                name = label
        except IndexError:
            # Ignore index error and supply missing legends
            for _ in range(index + 1 - len(labels)):
                labels.append('')
        return name

    # -----------------------------------------------------------------------
    # Trait methods

    def __colors_default(self):
        return cycle(['b', 'r', 'g', 'c', 'p', 'y'])

    # ----------------------------------------------------------------
    # Editable ROI labels

    def _edit_labels(self):
        proxy_names = [proxy.path for proxy in self.proxies[1:]]
        labels = self.model.labels

        config = {"names": proxy_names,
                  "labels": labels}
        content, ok = LabelTableDialog.get(config, parent=self.widget)
        if not ok:
            return

        # Update labels
        self.model.trait_set(labels=content["labels"])
        zipped = zip(content["names"], content["labels"])
        for index, (name, label) in enumerate(zipped, start=1):
            roi = self.get_roi(self.proxies[index])
            roi.label_text = label or name


def _is_compatible(binding):
    """Only instantiate the widget with an ImageBinding"""
    return isinstance(binding, ImageBinding)


@register_binding_controller(
    ui_name='Rect ROI Graph',
    klassname='RectRoiGraph',
    binding_type=(ImageBinding, VectorNumberBinding),
    priority=-200, can_show_nothing=False)
class RectRoiGraph(BaseRoiGraph):
    # Our Image Graph Model
    model = Instance(RectRoiGraphModel, args=())

    # -----------------------------------------------------------------------
    # Binding methods

    def add_proxy(self, proxy):
        binding = proxy.binding
        if isinstance(binding, (ImageBinding, VectorBoolBinding)):
            return

        roi = RectRoiProperty(color=next(self._colors),
                              label_text=self.get_label(proxy),
                              proxy=proxy)
        roi.add_to(self._plot)
        self.rois.append(roi)

        return True

    def value_update(self, proxy):
        # Update image
        if proxy is self.proxy:
            self._update_image(proxy.value)
            return

        roi = self.get_roi(proxy)
        if roi is not None:
            self._update_roi(roi, get_binding_value(proxy))


# ----------------------------------------------------------------------------
# ROI labels

CONFLICT_SUFFIX = " (Conflict)"


class LabelTableDialog(QDialog):
    """"""
    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.setModal(False)

        # Add table
        self._table = table = QTableWidget()
        table.setMinimumWidth(500)
        table.setColumnCount(2)
        table.setRowCount(len(config["names"]))
        table.setHorizontalHeaderLabels(["Property", "Labels"])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        # Add entries
        zipped = zip(config["names"], config["labels"])
        for row, (name, label) in enumerate(zipped):
            # proxy
            item = QTableWidgetItem(name)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            # label
            line_edit = QLineEdit(label)
            line_edit.setPlaceholderText(name)
            table.setCellWidget(row, 1, line_edit)

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
        dialog = LabelTableDialog(configuration, parent)
        result = dialog.exec_() == QDialog.Accepted
        content = {"names": dialog.names,
                   "labels": dialog.labels, }
        return content, result

    @property
    def names(self):
        return [self._table.item(row, 0).text()
                for row in range(self._table.rowCount())]

    @property
    def labels(self):
        labels = []
        for row in range(self._table.rowCount()):
            label = self._table.cellWidget(row, 1).text()
            if label:
                while label in labels:
                    label += CONFLICT_SUFFIX
            labels.append(label)
        return labels
