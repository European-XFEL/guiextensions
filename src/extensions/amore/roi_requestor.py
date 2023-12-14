#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
from functools import partial

from qtpy.QtCore import QObject

from karabo.native import Hash
from karabogui import messagebox
from karabogui.api import ROITool, is_device_online
from karabogui.logger import get_logger
from karabogui.request import call_device_slot

from .additional_color_bar import add_colorbar, remove_rois_colorbar
from .constants import HISTORY_HASH_PROPERTIES, LIGHT_RED

INDIVIDUAL_ROI_COLOR = [110, 255, 244]


class RoiRequestor(QObject):
    def __init__(self, image_annotate, parent=None):
        super().__init__(parent=parent)
        self.annotations_to_filter = []
        self._display_image_annotate = image_annotate
        self._canvas = None
        self._search_tool = self._display_image_annotate.searchingTool
        self._search_tool.get_data_button.clicked.connect(
            self._get_rois_from_interval)
        self._search_tool.plot_button.setEnabled(False)
        self._search_tool.plot_button.clicked.connect(
            partial(self.update_and_plot_rois, LIGHT_RED))

    def keep_track_of_previous_searchs(self):
        """
        In this method, both annotation and ROI type from previous searches
        are kept track of.
        """
        self._display_image_annotate.previous_search_annotation.append(
            self._search_tool.annotation_text.text())
        self._display_image_annotate.previous_search_tool.append(
            self._search_tool.annotation_type.currentText())

    def _get_rois_from_interval(self):
        self.annotations_to_filter = []
        self.annotations_to_filter.append(
            self._search_tool.annotation_text.text())
        info = Hash()
        info["type"] = self._display_image_annotate.remote_instance_id
        info["payload"] = Hash(
            "start",
            self._search_tool.start_time.dateTime(
            ).toPyDateTime().isoformat(),
            "end",
            self._search_tool.end_time.dateTime().
            toPyDateTime().isoformat())
        if self._search_tool.keep_all.isChecked():
            if (len(self._display_image_annotate.previous_search_annotation)
                    == 0):
                msg = ("Previous search do not contain any results. "
                       "No annotations found.")
                messagebox.show_warning(
                    msg, parent=self._display_image_annotate.widget)
            else:
                self.annotations_to_filter.append(
                    self._display_image_annotate.
                    previous_search_annotation[-1])
        info["annotation"] = self.annotations_to_filter
        info["roiType"] = ROITool[self._search_tool.
                                  annotation_type.currentText()]
        call_device_slot(self.on_update_annotation,
                         self._display_image_annotate.remote_instance_id,
                         "requestHistoricData", info=info)
        self.keep_track_of_previous_searchs()

    def on_update_annotation(self, success, reply):
        if success is True:
            if reply["payload"]["len"] == 0:
                device_id = self._display_image_annotate.remote_instance_id
                msg = ("There are no reference values saved "
                       f"for {device_id}, annotation and ROI type.")
                messagebox.show_warning(
                    msg, title='No ROIs in Device',
                    parent=self._search_tool)
                self._search_tool.plot_button.setEnabled(False)
            else:
                self._search_tool.plot_button.setEnabled(True)
        device_id = self._display_image_annotate.remote_instance_id
        device_online = is_device_online(
            self._display_image_annotate.remote_instance_id)
        if not device_online:
            messagebox.show_error(
                f"Request for {device_id} timed out!",
                title='Coordinate device not instantiated',
                parent=self._display_image_annotate.widget)
            get_logger().info("Coordinate device not instantiated")
            return

    def update_and_plot_rois(self, color):
        # Retrieve and save the regions of interest (ROIs) from device node.
        self._display_image_annotate.saved_rois = {
            history_key: self._display_image_annotate._get_value(
                self._display_image_annotate.historic_proxy.value,
                history_key) for history_key in HISTORY_HASH_PROPERTIES}
        # Determine the type of ROI tool (Cross or Rect).
        roi_tool = ROITool[self._search_tool.
                           annotation_type.currentText()]
        # Calculate delta dates and create a lookup table for colors.
        self._display_image_annotate._calculate_delta_dates()
        lut_colors = self._display_image_annotate.create_lut_colors(color)
        self._display_image_annotate.saved_rois["lut"] = lut_colors
        # Remove existing color bar if present.
        if hasattr(self._display_image_annotate.widget, "_rois_colorbar"):
            remove_rois_colorbar(self._display_image_annotate.widget)
        # Remove existing ROIs from the plot and then plot the updated ROIs.
        self._display_image_annotate.remove_rois_from_plot()
        self._display_image_annotate.plot_rois()
        self._display_image_annotate.widget.roi.selected.emit(
            roi_tool)
        add_colorbar(self._display_image_annotate)
