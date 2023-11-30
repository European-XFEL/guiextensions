#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################


import numpy as np
from pyqtgraph import AxisItem, GraphicsWidget, ImageItem
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import QGraphicsGridLayout, QInputDialog, QMenu

from karabogui.fonts import get_qfont
from karabogui.graph.common.const import X_AXIS_HEIGHT
from karabogui.graph.image.colorbar import ColorViewBox

from .constants import LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED, MULTICOLOR
from .utils import create_lut, plot_rois, roi_filter

# -----
# Extra colorbar showing the dates associated to each ROI
# -----------


class ColorBarWidgetDates(GraphicsWidget):
    levelsChanged = Signal(object)

    def __init__(self, imageItem, oldest_date,
                 days_axes, image_annotate, parent=None):
        self._display_image_annotate = image_annotate
        self.selected_color = LIGHT_RED
        super().__init__(parent=parent)
        self.imageItem = imageItem
        self.levels = min_level, max_level = [0, oldest_date]

        data = np.linspace(min_level, max_level, oldest_date)[None, :]
        axis = np.linspace(min_level, max_level, oldest_date)
        self.grid_layout = QGraphicsGridLayout(self)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 40, 0, 0)

        self.vb = ColorViewBox(parent=self)
        self.vb.menu = self._create_menu()
        self.vb.setToolTip("Delta days: difference with respect current date")

        self.barItem = ImageItem(parent=self)
        self.barItem.setImage(data)
        self.vb.scene().sigPrepareForPaint.connect(self.vb.prepareForPaint)
        self.vb.addItem(self.barItem)
        self.grid_layout.addItem(self.vb, 1, 0)
        self.vb.setYRange(*self.levels, padding=0)
        self.lut = create_lut(self.selected_color)
        self.barItem.setLookupTable(self.lut)
        font = get_qfont()
        font.setPointSize(8)

        self.axisItem = AxisItem(orientation='right', parent=self)
        day_list = []
        day_list_minor = []

        for day in list(set(sorted(days_axes))):
            day_list.append((day + 0.5, str("- " + str(day) + " Days")))

        for date in axis:
            day_list_minor.append(
                (int(date) + 0.5, str("")))

        days_list = [day_list, day_list_minor]
        self.axisItem.setTicks(days_list)
        self.axisItem.setStyle(tickFont=font)
        self.axisItem.linkToView(self.vb)
        self.grid_layout.addItem(self.axisItem, 1, 1)
        self.setLayout(self.grid_layout)

    # ---------------------------------------------------------------------
    # PyQt slots

    @Slot()
    def _show_levels_dialog(self):
        items = ["Monochromatic degradate (Red)",
                 "Monochromatic degradate (Green)",
                 "Monochromatic degradate (Blue)",
                 "Multicolor mode"]

        item, ok = QInputDialog().getItem(None, "Select Color",
                                          "Season:", items, 0, False)
        if ok is True:
            if item == "Monochromatic degradate (Green)":
                self.selected_color = LIGHT_GREEN
            elif item == "Monochromatic degradate (Red)":
                self.selected_color = LIGHT_RED
            elif item == "Monochromatic degradate (Blue)":
                self.selected_color = LIGHT_BLUE
            elif item == "Multicolor mode":
                self.selected_color = MULTICOLOR
            # We change the color of colorbar and apply the changes
            self.lut = create_lut(self.selected_color)
            self.barItem.setLookupTable(self.lut)
            # And now we change the ROI color,
            # because each ROI has a different color depending on when
            # it was saved, we removed it and we plot it again
            # instead of iteration over _rois and updating the color.
            self._display_image_annotate.remove_rois_from_plot()
            # First we iterate over the ROIS got from the past,
            # Get history from interval.
            roi_dict_list = roi_filter(
                self._display_image_annotate, self.selected_color)
            plot_rois(self._display_image_annotate, roi_dict_list)

    # ---------------------------------------------------------------------
    # Qt Events

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._show_levels_dialog()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    # ---------------------------------------------------------------------
    # Public methods

    def set_margins(self, top=None, bottom=None):
        """Sets top and bottom margins of the colorbar. This depend on the
        axis size of the main plot."""
        if top is None:
            _, top, _, _ = self.grid_layout.getContentsMargins()
        if bottom is None:
            _, _, _, bottom = self.grid_layout.getContentsMargins()

        self.grid_layout.setContentsMargins(0, top, 0, bottom)

    # ---------------------------------------------------------------------
    # Private methods

    def _create_menu(self):
        menu = QMenu()
        menu.addAction("Set colors", self._show_levels_dialog)
        return menu


def add_colorbar(image_annotate):
    # Enable the standard colorbar of this widget
    # We add an additional colorbar for the ROIs
    plotItem = image_annotate.widget.plotItem
    image_annotate.widget._rois_colorbar = ColorBarWidgetDates(
        image_annotate.delta_days_filtered, int(
            np.max(image_annotate.delta_days_filtered)) + 1,
        image_annotate.delta_days_filtered,
        image_annotate, parent=plotItem)

    top_axis_checked = plotItem.getAxis("top").style["showValues"]
    top_margin = X_AXIS_HEIGHT * top_axis_checked

    bot_axis_checked = plotItem.getAxis("bottom").style["showValues"]
    bottom_margin = X_AXIS_HEIGHT * bot_axis_checked

    image_annotate.widget._rois_colorbar.set_margins(
        top=top_margin, bottom=bottom_margin)
    image_annotate.widget._rois_colorbar.levelsChanged.connect(
        plotItem.set_image_levels)

    image_annotate.widget.image_layout.addItem(
        image_annotate.widget._rois_colorbar, row=1, col=3)
    image_annotate.widget.image_layout.ci.layout.setColumnStretchFactor(2, 1)

    image_annotate.widget.add_colormap_action()

    return image_annotate.widget._rois_colorbar


def remove_rois_colorbar(widget):
    if widget._rois_colorbar is not None:
        widget.image_layout.removeItem(widget._rois_colorbar)
        widget.image_layout.ci.layout.setColumnStretchFactor(1, 3)
        widget._rois_colorbar.deleteLater()
        widget._rois_colorbar = None
        widget.remove_colormap_action()
