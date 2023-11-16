#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import datetime
import re

import numpy as np
from pyqtgraph import ColorMap

from karabogui.api import ROITool, messagebox

from .constants_keys import HISTORY_HASH_PROPERTIES

# ---------------------------------------------------------------------
# Functions associated to the icons plotting
# ---------------------------------------------------------------------


def roi_filter(image_annotate, color):
    # Adding the ROI (Crosshair/rectangle) coordinates saved in the device,
    # following the structure of add method of BaseROIController.
    # Filtering by annotation
    _filter_by_annotation(image_annotate)
    # Create a lut based on the dates associated to the filtered values
    lut_colors = _create_lut_colors(image_annotate, color)
    # Individually plotting the filtered result
    roi_filtered = list(image_annotate.saved_rois.values())
    roi_filtered.append(lut_colors)
    return roi_filtered


def roi_plot(image_annotate, roi_dict_list):
    for j in range(len(roi_dict_list[0])):
        individual_roi_info = []
        for i in range(len(roi_dict_list)):
            individual_roi_info.append(roi_dict_list[i][j])
        image_annotate.plotting(individual_roi_info)


def _filter_by_annotation(image_annotate):
    # This function allows the user to filter the value based on
    # the specified annotation and tool.
    image_annotate.saved_rois = {
        history_key: image_annotate._get_value(
            image_annotate.historic_proxy.value, history_key)
        for history_key in HISTORY_HASH_PROPERTIES}
    search_values = [image_annotate.searchingTool.ui_annotation_value]
    if (image_annotate.searchingTool.ui_keep_all.isChecked()):
        if len(image_annotate.previous_search_annotation) == 0:
            msg = ("Previous search do not contain any results. "
                   "No annotations found.")
            messagebox.show_warning(msg, parent=image_annotate.widget)
        else:
            search_values.append(
                [image_annotate.previous_search_annotation[-1]])
    # Collecting the indices of annotations containing a specified string
    # from the "Search by Annotation" box and matching the annotation
    # type.
    # Then we interesct both lists, to get common elements
    search_indices, indices_to_remove = _get_indices(
        image_annotate, search_values)
    _calculate_delta_dates(image_annotate, search_indices)
    _remove_no_matched_results(image_annotate, indices_to_remove)


def _get_indices(image_annotate, search_values):
    roi_tool = ROITool[image_annotate.searchingTool.
                       ui_annotation_type_value]
    for search_annotation in search_values:
        annotation_indices = (
            [i for i, x in enumerate(image_annotate.saved_rois["annotation"])
             if re.search(search_annotation, x, flags=re.IGNORECASE)])
        type_indices = [i for i, x in enumerate(
            image_annotate.saved_rois["roiTool"]) if x == roi_tool]
        search_indices = (annotation_indices and type_indices)
    indices = np.array(range(len(image_annotate.saved_rois["annotation"])))
    indices_to_remove = np.delete(indices, search_indices)
    return search_indices, indices_to_remove


def _calculate_delta_dates(image_annotate, search_indices):
    """
    Calculating the number of days between the current date and
    the date the ROI was saved.
    image_annotate: object of the class DisplayImageAnnotate
    search_indices: indices obtained after filtering by annotation and type
    """
    image_annotate.delta_days_filtered = []
    for i in search_indices:
        delta_time = ((datetime.datetime.now() -
                       datetime.datetime.strptime(
            image_annotate.saved_rois["date"][i], '%d/%m/%Y %H:%M:%S')))
        delta_day = delta_time.days
        image_annotate.delta_days_filtered.append(delta_day)


def _remove_no_matched_results(image_annotate, indices_to_remove):
    if len(indices_to_remove) > 0:
        for roi_key in HISTORY_HASH_PROPERTIES:
            image_annotate.saved_rois[roi_key] = np.delete(
                image_annotate.saved_rois[roi_key], indices_to_remove)


def _create_lut_colors(image_annotate, color):
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
    lut = cmap.getLookupTable(alpha=False)
    return lut


def display_saved_data(selected_roi):
    selected_roi.setToolTip(
        "Saved: " + str((selected_roi.saved_date)))
