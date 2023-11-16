#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from functools import partial

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QDialog

from karabo.native import Hash
from karabogui import messagebox
from karabogui.api import ROITool, is_device_online
from karabogui.logger import get_logger
from karabogui.request import call_device_slot

from .additional_color_bar import add_colorbar_rois, remove_rois_colorbar
from .aux_filtering_and_plotting import roi_filter, roi_plot
from .constants_keys import LIGHT_RED

INDIVIDUAL_ROI_COLOR = [110, 255, 244]


class RoiRequestor(QObject):
    def __init__(self, image_annotate, parent=None):
        super().__init__(parent=parent)

        self._display_image_annotate = image_annotate
        self._canvas = None
        self._display_image_annotate.widget.layout().addWidget(
            self._display_image_annotate.coordinatesTool, 1, 0, 1, 2)
        (self._display_image_annotate.coordinatesTool.
            ui_get_coordinates.clicked.connect(
                self._get_rois_from_interval))
        (self._display_image_annotate.coordinatesTool.
         ui_get_last_coordinates.clicked.connect(
             partial(self._display_image_annotate.update_from_remote, True)))

    def keep_track(self):
        self._display_image_annotate.previous_search_annotation.append(
            self._display_image_annotate.searchingTool.ui_annotation_value)
        self._display_image_annotate.previous_search_tool.append(
            self._display_image_annotate.searchingTool.
            ui_annotation_type_value)

    def _get_rois_from_interval(self):
        info = Hash()
        info["type"] = self._display_image_annotate.remote_instance_id
        info["payload"] = Hash(
            "start",
            self._display_image_annotate.coordinatesTool.ui_start_time.
            dateTime().toPyDateTime().isoformat(),
            "end",
            self._display_image_annotate.coordinatesTool.ui_end_time.
            dateTime().toPyDateTime().isoformat())
        call_device_slot(self.on_update_annotation,
                         self._display_image_annotate.remote_instance_id,
                         "requestHistoricData", info=info)

    def on_update_annotation(self, success, reply):
        # We check that we asked for historical/previous values
        if success is True:
            self.search = True
            self._display_image_annotate.widget.roi.selected.emit(
                ROITool.NoROI)
            self.filtering_and_plotting(LIGHT_RED)
        device_id = self._display_image_annotate.remote_instance_id
        device_online = is_device_online(
            self._display_image_annotate.remote_instance_id)
        if not device_online:
            messagebox.show_error(
                (f"Request for {device_id}"
                 " timed out!"),
                title='Coordinate device not instantiated',
                parent=self._display_image_annotate.widget)
            get_logger().info("Coordinate device not instantiated")
            return

    def filtering_and_plotting(self, color):
        if (self._display_image_annotate.searchingTool.exec_() ==
                QDialog.Accepted):
            self._display_image_annotate.widget.roi.selected.emit(
                ROITool.NoROI)
            # Set the ROItool to the proper value set by the user
            # Removing ROIS obtained in a previous search
            roi_tool = ROITool[self._display_image_annotate.searchingTool.
                               ui_annotation_type_value]
            roi_dict_list = roi_filter(
                self._display_image_annotate, color)
            # We keep track of the searches in case the user
            # wants to keep previous values.
            self.keep_track()
            if hasattr(self._display_image_annotate.widget, "_colorbarl"):
                remove_rois_colorbar(self._display_image_annotate.widget)
            if len(roi_dict_list[0]) > 0:
                self._display_image_annotate.remove_rois_from_plot()
                roi_plot(self._display_image_annotate, roi_dict_list)
                self._display_image_annotate.widget.roi.selected.emit(
                    roi_tool)
                add_colorbar_rois(self._display_image_annotate)
            else:
                self._display_image_annotate.no_rois_found_message(
                    "No reference values saved from this"
                    " device and ROI type")
                # And we unselect the ROItool
                self._display_image_annotate.widget.roi.selected.emit(
                    ROITool.NoROI)
            # We have to first remove all the previous ROIS
            # anyway because their color depend on their
            # "relative" date they were saved.
