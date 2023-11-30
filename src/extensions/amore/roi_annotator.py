#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import datetime
from functools import partial

from pyqtgraph import functions as fn
from qtpy.QtCore import QObject

from karabo.native import Hash
from karabogui import messagebox
from karabogui.api import is_device_online
from karabogui.logger import get_logger
from karabogui.request import call_device_slot

from .constants import TOOL_MAP, TOOL_MAP_NUMBERS
from .utils import display_saved_data

INDIVIDUAL_ROI_COLOR = [110, 255, 244]


class RoiAnnotator(QObject):

    def __init__(self, image_annotate, parent=None):
        super().__init__(parent=parent)
        self._display_image_annotate = image_annotate
        self._canvas = None

    def updateSavedColor(self, selected_roi):
        if not selected_roi.mouseHovering:
            return selected_roi.pen
        pen = fn.mkPen(255, 255, 0)
        pen.setWidthF(3)
        if selected_roi.currentPen != pen:
            selected_roi.currentPen = pen
            selected_roi.update()

    def send_selected_coordinates(self, selected_roi):
        selected_annotation_name = selected_roi.name
        self.selected_roi = selected_roi
        # If the user has not change the name of the ROI
        # we save it as Region of Interest.
        if len(selected_annotation_name) == 0:
            selected_annotation_name = "Region of Interest"
        # Getting the information on the ROI that is going to be saved
        # We distinguish between the CrosshairROI and RectROI because
        # the RectROI has two extra values, the rectangle size.
        info = Hash()
        info["type"] = self._display_image_annotate.remote_instance_id
        roi_class_name = TOOL_MAP[
            self._display_image_annotate.widget.roi.current_tool].__name__
        roi_class_number = TOOL_MAP_NUMBERS[
            self._display_image_annotate.widget.roi.current_tool]
        info_hash = self.create_roi_basic_hash(
            self._display_image_annotate.widget.roi._current_item[
                self._display_image_annotate.widget.roi.current_tool],
            roi_class_name)

        info_hash["annotation"] = selected_annotation_name
        info_hash["date"] = str(
            datetime.datetime.now())
        info_hash["roiTool"] = roi_class_number
        info["payload"] = info_hash
        remote_id = self._display_image_annotate.remote_instance_id
        call_device_slot(self.on_update_single_annotation, remote_id,
                         "sendSelectedROI", info=info)

    def setting_roi_properties(self, selected_roi):
        # First we add the selected roi, sent to the device
        # to the reference_rois list.
        self._display_image_annotate._reference_rois[
            self._display_image_annotate.widget.roi.current_tool].append(
            selected_roi)
        selected_roi.saved_date = (
            (datetime.datetime.now()))
        # We assign this color, the highest bright
        # color in the default scale.
        color = INDIVIDUAL_ROI_COLOR
        # Now we change the default color of the ROI
        selected_roi.pen = fn.mkPen(color)
        # And we fix its position
        selected_roi.translatable = False
        selected_roi.removable = False
        selected_roi.sigHoverEvent.connect(
            partial(display_saved_data, selected_roi))

    def on_update_single_annotation(self, success, reply):
        # We check that we asked for historical/previous values
        if success is True:
            self.setting_roi_properties(self.selected_roi)
            self.updateSavedColor(self.selected_roi)
        device_online = is_device_online(
            self._display_image_annotate.remote_instance_id)
        if not device_online:
            remote_id = self._display_image_annotate.remote_instance_id
            messagebox.show_error(
                f"Request for {remote_id}  timed out.")
            get_logger().info("Coordinate device not instantiated")
            return

    def create_roi_basic_hash(self, roi, roi_type):
        info_hash = Hash()
        info_hash["horizontal"] = roi.coords[0]
        info_hash["vertical"] = roi.coords[1]
        if roi_type == "RectROI":
            info_hash["horizontalSize"] = roi.coords[2]
            info_hash["verticalSize"] = roi.coords[3]
        elif roi_type == "CrosshairROI":
            info_hash["horizontalSize"] = 0
            info_hash["verticalSize"] = 0
        return info_hash
