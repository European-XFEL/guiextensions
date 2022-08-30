#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import datetime
import re

import numpy as np
from pyqtgraph import ColorMap

from karabogui import messagebox
from karabogui.api import is_device_online
from karabogui.graph.common.api import ROITool
from karabogui.logger import get_logger

from .constants_keys import HISTORY_KEYS, INDIVIDUAL_KEYS, INDIVIDUAL_ROI_COLOR

# ---------------------------------------------------------------------
# Functions associated to the icons plotting
# ---------------------------------------------------------------------


def roi_filtering(image_annotate, color):
    # Adding the ROI (Crosshair/rectangle) coordinates saved in the device,
    # following the structure of add method of BaseROIController.
    # Filtering by annotation
    information_filtered = _filtering_by_annotation(image_annotate)
    # Create a lut based on the dates associated to the filtered values
    lut_colors = _creating_lut_colors(
        image_annotate, color)
    # Individually plotting the filtered result
    roi_dict_list = []
    for key in information_filtered:
        roi_dict_list.append(information_filtered[key])
    roi_dict_list.append(lut_colors)
    return roi_dict_list


def roi_plotting(image_annotate, roi_dict_list):
    for j in range(len(roi_dict_list[0])):
        individual_roi_info = []
        for i in range(len(roi_dict_list)):
            individual_roi_info.append(roi_dict_list[i][j])
        image_annotate.plotting(individual_roi_info, True)


def checking_for_previous_searches(roi_requestor, annot):
    is_filtered_previous = None
    # if hasattr(self.searchingTool, "previous_annotation"):
    if roi_requestor.searchingTool.ui_keep_all.isChecked() is True:
        is_filtered_previous = individual_filtering_previous(
            roi_requestor, annot)
        if len(is_filtered_previous) > 0:
            is_filtered_previous = is_filtered_previous[0]
        # else:
        #    is_filtered_second = None
    return is_filtered_previous


def individual_filtering_previous(roi_requestor, annot):
    # Comparing current ROI with previous
    # search values
    is_filtered_previous_list = []
    for i in range(len(roi_requestor.previous_search_annotation)):
        is_filtered_previous = (individual_filtering(
            roi_requestor.previous_search_annotation[i], annot))
        if (roi_requestor.previous_search_tool[i]
                == roi_requestor.searchingTool.
                ui_annotation_type.currentText()):
            if is_filtered_previous:
                is_filtered_previous_list.append(is_filtered_previous)
    return is_filtered_previous_list


def individual_filtering(search_annotation, annot):
    # Now we finally start filtering by the text set by the user
    if len(search_annotation) == 0:
        # If the user did not write anything, then we dont
        # filter
        match = True
    else:
        match_low = re.search(
            search_annotation.lower(), annot.lower())
        match_up = re.search(
            search_annotation.upper(), annot.upper())
        match = (match_low or match_up)
    return match


def update_from_remote(image_annotate, flag=True):
    color = INDIVIDUAL_ROI_COLOR
    info = []
    device_online = (is_device_online(image_annotate.remote_instance_id))
    if device_online:
        for individual in INDIVIDUAL_KEYS:
            info.append(image_annotate.proxy_dictionary[individual].value)
        info.append(color)
        image_annotate.widget.roi.selected.emit(ROITool.NoROI)
        image_annotate.widget.roi.selected.emit(
            image_annotate.proxy_dictionary["roiTool"].value)
        image_annotate.plotting(info, flag)
    else:
        messagebox.show_warning("Device no instantiated",
                                title='Device no instantiated?')


def removing_rois_from_plot(roi_requestor):
    # If we allow to remove individual ROIs then we
    # need to add a try/except so the code does not
    # crash while trying to remove unexisting ROIS.
    for item in roi_requestor._reference_rois[
            roi_requestor.widget.roi.current_tool]:
        try:
            if item.textItem:
                roi_requestor.widget.roi.plotItem.vb.removeItem(item.textItem)
            roi_requestor.widget.roi.plotItem.vb.removeItem(item)
        except AttributeError:
            get_logger().info("No (latest) ROI in device")


def _filtering_by_annotation(image_annotate):
    # This function filters the value by the annotation and tool
    # entered by the user
    image_annotate.delta_days_filtered = []
    info_filtered_rois_from_interval = {}
    for key in HISTORY_KEYS:
        info_filtered_rois_from_interval[key] = []
    for hor, ver, annot, date, roi_type, hor_size, ver_size in zip(
            image_annotate.proxy_dictionary_history["historyHorizontal"].value,
            image_annotate.proxy_dictionary_history["historyVertical"].value,
            image_annotate.proxy_dictionary_history["historyAnnotation"].value,
            image_annotate.proxy_dictionary_history["historyDates"].value,
            image_annotate.proxy_dictionary_history["historyRoiTool"].value,
            image_annotate.proxy_dictionary_history[
                "historyHorizontalSize"].value,
            image_annotate.proxy_dictionary_history[
                "historyVerticalSize"].value
    ):
        # We have to check if the element has been filtered
        is_filtered = individual_filtering(
            image_annotate.searchingTool.ui_annotation_value, annot)
        is_filtered_second = checking_for_previous_searches(
            image_annotate, annot)
        # And now that we know that it has been filtered we have
        # to know, when, in days from today; to asign the correct colo

        if (is_filtered or is_filtered_second):
            roi_summary = [hor, ver, annot, date, roi_type, hor_size, ver_size]
            roi_keys = image_annotate.proxy_dictionary_history.keys()
            # Time difference
            delta_time = ((datetime.datetime.now() -
                           datetime.datetime.strptime(
                               date, '%d/%m/%Y %H:%M:%S')))
            if roi_type == image_annotate.annotation_type:
                for roi_value, roi_key in zip(roi_summary, roi_keys):
                    info_filtered_rois_from_interval[roi_key].append(roi_value)
                delta_day = delta_time.days
                image_annotate.delta_days_filtered.append(delta_day)
    return info_filtered_rois_from_interval


def _creating_lut_colors(image_annotate, color):
    # This function creates a LUT, and assign a colour
    # to each ROI depending on the day it was saved.
    lut_colors = []
    if len(image_annotate.delta_days_filtered) > 0:
        delta_max = (np.max(image_annotate.delta_days_filtered))
        # Normalizing the dates wrt the oldest saved ROI
        if delta_max == 0:
            delta_days_normalized = np.zeros(
                len(image_annotate.delta_days_filtered))
        else:
            delta_days_normalized = np.array(
                image_annotate.delta_days_filtered)/delta_max*511
        # Createing the lut
        color_number = []
        lut = _create_lut(color)
        # Find the color associated to each ROI
        for day in delta_days_normalized:
            color_number.append(int(day))
            color = (lut[int(day)][0], lut[int(day)][1], lut[int(day)][2])
            lut_colors.append(color)
    return lut_colors


def _create_lut(color):
    colors = []
    for i, c in enumerate(color):
        colors.append(tuple([cc * 255 for cc in c] + [1]))
    cmap = ColorMap(np.linspace(0, 1.0, len(colors)), colors)
    lut = cmap.getLookupTable(mode="rgb", alpha=False)
    return lut


def display_saved_data(selected_roi):
    selected_roi.setToolTip(
        "Saved: " + str((selected_roi.saved_date)))
