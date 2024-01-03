#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
import datetime
from collections import defaultdict
from functools import partial

import numpy as np
from pyqtgraph import Point, functions as fn
from traits.api import Bool, Dict, Enum, Float, Instance, List, String, WeakRef

from karabo.common.scenemodel.api import (
    build_graph_config, restore_graph_config)
from karabo.common.states import State
from karabogui.api import (
    BaseBindingController, ImageBinding, KaraboImageNode, KaraboImagePlot,
    KaraboImageView, KaraboImageViewBox, MouseMode, PropertyProxy, ROITool,
    WidgetNodeBinding, get_binding_value, messagebox,
    register_binding_controller)
from karabogui.graph.common.api import AuxPlots

from ..models.api import ROIAnnotateModel
from .annotation_dialog_and_display import (
    AnnotationSearchDialog, DisplayTool, DisplayToolset)
from .constants import (
    HISTORY_HASH_PROPERTIES, HISTORY_HASH_TYPES, LUT_LENGTH, TOOL_MAP)
from .roi_annotator import RoiAnnotator
from .roi_requestor import RoiRequestor
from .utils import create_lut, display_saved_data

INDIVIDUAL_ROI_COLOR = [110, 255, 244]


def is_compatible(binding):
    """Only allow images for this controller"""
    return isinstance(binding, ImageBinding)


@register_binding_controller(
    ui_name='ROI Annotate',
    klassname='ROIAnnotate',
    binding_type=(ImageBinding, WidgetNodeBinding),
    is_compatible=is_compatible,
    can_show_nothing=False, can_edit=False)
class DisplayImageAnnotate(BaseBindingController):
    # the following are copied over from the existing widget
    # (original image annotation)
    # Adding all the tools needed to play with the annotations
    _roi_annotator = WeakRef(RoiAnnotator)
    _roi_requestor = WeakRef(RoiRequestor)
    _display_toolset = WeakRef(DisplayToolset)
    _pause_image = Bool(False)

    previous_search_annotation = List()
    previous_search_tool = List()
    searchingTool = Instance(AnnotationSearchDialog, args=())
    annotation_type = Float(2)
    delta_max = Float(5)
    delta_days_filtered = List()
    saved_rois = Dict()
    search = Bool(False)

    # plot
    _plot = WeakRef(KaraboImagePlot)
    model = Instance(ROIAnnotateModel, args=())
    _image_node = Instance(KaraboImageNode, args=())
    _mouse_mode = Enum(*MouseMode)
    _viewbox = WeakRef(KaraboImageViewBox)
    _reference_rois = defaultdict(list)

    # The ROI proxy instance ID
    remote_instance_id = String()
    # The roi proxys holding the roi information:
    # annotation and historicAnnotation
    roi_proxy = Instance(PropertyProxy)
    historic_proxy = Instance(PropertyProxy)
    # The image proxy holding the camera/image information
    image_proxy = Instance(PropertyProxy)

    # ------------------------------------------
    # Creating widget

    def create_widget(self, parent):
        self.widget = KaraboImageView(parent=parent)

        # Saving changes in the scene:
        # Design mode, ROI Annotate: Properites, Set ROI and Aux
        self.widget.stateChanged.connect(self._change_model)
        self.widget.add_colorbar()
        self.widget.add_roi()
        self.widget.add_aux(plot=AuxPlots.ProfilePlot, smooth=True)

        # Adding QActions
        self.widget.add_axes_labels_dialog()
        self.widget.add_transforms_dialog()

        # Adding the Play/Pause controller and the Annotation ToolSet
        tb = self.widget.add_toolbar()
        tb.register_toolset(DisplayTool, DisplayToolset)

        # Get a reference for our plotting
        self._plot = self.widget.plot()
        self._viewbox = self._plot.getViewBox()
        self._mouse_mode = self._viewbox.mouse_mode

        # Adding the display Toolset (play/pause)
        self._display_toolset = tb.add_toolset(DisplayTool)
        self._display_toolset.on_trait_change(self._display,
                                              "current_tool")
        # The sending of ROIs is delegated to the RoiAnnotator,
        # which interacts with the rest of the system via slots.
        self._roi_annotator = RoiAnnotator(self, parent=parent)
        # The requesting of ROIs from interval is delegated to
        # the RoiRequestor.
        self._roi_requestor = RoiRequestor(self, parent=parent)
        # Restore the model information
        self.widget.restore(build_graph_config(self.model))
        return self.widget

    def add_proxy(self, proxy):
        if proxy.binding is not None:
            if (proxy.binding.display_type == "WidgetNode|HistoricAnnotation"
                    and self.historic_proxy is None):
                self.historic_proxy = proxy
                self.remote_instance_id = proxy.root_proxy.device_id
            if (proxy.binding.display_type == "WidgetNode|CoordinateAnnotation"
                    and self.roi_proxy is None):
                self.roi_proxy = proxy
            if (proxy.binding.display_type == "ImageData" and
                    self.image_proxy is None):
                self.image_proxy = proxy
        else:
            # Getting the DEVICE ID, also when it's not instantiated.
            self.remote_instance_id = proxy.root_proxy.device_id
        return True

    def binding_update(self, proxy):
        if self.roi_proxy is None:
            self.add_proxy(proxy)
        if self.historic_proxy is None:
            self.add_proxy(proxy)
        if self.image_proxy is None:
            self.add_proxy(proxy)

    def value_update(self, proxy):
        if proxy is self.roi_proxy:
            # The current remote proxy does not display
            # any error message when device is without value.
            self.update_from_remote()
        elif proxy is self.historic_proxy:
            # Update past values only when the user requests it.
            pass
        else:
            image_data = proxy.value
            self._image_node.set_value(image_data)

            if not self._image_node.is_valid:
                return
            array = self._image_node.get_data()

            if self._pause_image is False:
                self._plot.setData(array)

    # --------------
    # model

    def _change_model(self, content):
        # MODEL does not saved reference values,
        # to avoid confusion with the color codes.
        self.model.trait_set(**restore_graph_config(content))

    # ----------------------------------------
    # Functionalities associated with new icons
    # Playing/Pause the image

    def _display(self, display_tool):
        if display_tool is DisplayTool.PlayImage:
            self._pause_image = False
            self._display_toolset.select(DisplayTool.NoTool)
        elif display_tool is DisplayTool.PauseImage:
            self._pause_image = True
            self._display_toolset.select(DisplayTool.NoTool)
        elif display_tool is DisplayTool.SendSelectCross:
            # Send the selected cross to the ROIAnnotation device.

            # Determine the currently selected ROI.
            selected_roi = self.widget.roi._current_item[
                self.widget.roi.current_tool]
            if selected_roi:
                # Check if the ROI has already been saved.
                # If not, send selected coordinates.
                if (selected_roi not in
                        self._reference_rois[self.widget.roi.current_tool]):
                    self._roi_annotator.send_selected_coordinates(selected_roi)
                else:
                    # Display a warning if the ROI is already saved.
                    messagebox.show_alarm(
                        "ROI already saved, "
                        "please select a ROI before sending it to the device.",
                        parent=self.widget)
            else:
                # Display a warning if no ROI is selected.
                messagebox.show_alarm(
                    "Nothing selected, "
                    "please select a ROI before sending it to the device.",
                    parent=self.widget)
            self._display_toolset.select(
                DisplayTool.NoTool)
        elif display_tool is DisplayTool.DisplayInterval:
            self.searchingTool.exec_()
            self._display_toolset.select(
                DisplayTool.NoTool)
        elif display_tool is DisplayTool.NoTool:
            # Reset the display tool.
            self._viewbox.set_mouse_mode(self._mouse_mode)

    def state_update(self, proxy):
        state = self._get_state(proxy)
        if State(state) is State.RUNNING:
            self._pause_image = False

    def _get_state(self, proxy):
        root_proxy = proxy.root_proxy
        state = get_binding_value(root_proxy.state_binding)
        return state

    def plotting(self, info):
        horizontal_coordinate = info[0]
        vertical_coordinate = info[1]
        annotation = info[2]
        saved_date = info[3]
        current_tool = info[4]
        size = [info[5], info[6]]
        color = info[7]
        self.add_rois_to_plot(current_tool,
                              [horizontal_coordinate, vertical_coordinate],
                              saved_date, color, size=size,
                              name=annotation)
        self.widget.roi.show(self.widget.roi.current_tool)

    def update_from_remote(self):
        color = INDIVIDUAL_ROI_COLOR
        info = []
        if self.roi_proxy is None:
            msg = f"Device {self.remote_instance_id} not instantiated"
            messagebox.show_warning(
                msg, title='No ROIs in Device', parent=self.widget)
            return
        for prop, prop_type in zip(HISTORY_HASH_PROPERTIES,
                                   HISTORY_HASH_TYPES):
            prop_value = self._get_value(self.roi_proxy.value,
                                         prop)
            # There are values in the node with the correct type
            if (prop_value is not None and (type(prop_value) is prop_type)):
                info.append(
                    self._get_value(self.roi_proxy.value,
                                    prop))
            # There are values in the node property but the wrong type
            elif type(prop_value) is prop_type:
                messagebox.show_error(
                    f"Wrong data type for {prop}", parent=self.widget)
                return
        info.append(color)
        self.widget.roi.selected.emit(ROITool.NoROI)
        self.widget.roi.selected.emit(
            self._get_value(self.roi_proxy.value,
                            "roiTool"))
        self.plotting(info)

    def add_rois_to_plot(self, tool, pos, date, color, size=None,
                         name='', ignore_bounds=False, current_item=True):
        roi_class = TOOL_MAP[tool]
        pos = Point(pos)
        selected_pen = fn.mkPen(color)
        if size is not None:
            roi_item = roi_class(pos=pos, size=size, name=name,
                                 pen=selected_pen)
        else:
            roi_item = roi_class(pos=pos, name=name, pen=selected_pen)
        scaleSnap = (getattr(self.widget.roi, '_scale_snap', None)
                     or getattr(self.widget.roi, 'scaleSnap'))
        translateSnap = (getattr(self.widget.roi, '_translate_snap', None)
                         or getattr(self.widget.roi, 'translateSnap'))

        roi_item.scaleSnap = scaleSnap
        roi_item.translateSnap = translateSnap
        # ROIs cannot be removed to avoid misunderstandings
        # since they can only be hidden from the plot
        # but not deleted from the history.
        roi_item.translatable = False
        # Standard signals are connected including the sigHoverEvent
        # that displays when the data is saved.
        roi_item.sigRegionChangeStarted.connect(
            self.widget.roi._set_current_item)
        roi_item.sigRegionChanged.connect(self.widget.roi.update)
        roi_item.sigRemoveRequested.connect(
            self.widget.roi._remove_roi_item)
        roi_item.sigClicked.connect(self.widget.roi._set_current_item)
        roi_item.sigHoverEvent.connect(
            self.widget.roi._set_current_item)
        roi_item.sigHoverEvent.connect(
            partial(display_saved_data, roi_item))
        roi_item.saved_date = date
        # Bookkeeping. Add the current ROI
        # to the list of existing ROIs, tool specific.
        self.widget.roi._rois[tool].append(roi_item)
        self._reference_rois[tool].append(roi_item)

        # Add the ROI item to the plot
        self.widget.roi._add_to_plot(roi_item, ignore_bounds)

        if current_item:
            self.widget.roi._current_tool = tool
            self.widget.roi._set_current_item(roi_item, update=False)
            # Set as current item, in which affects the aux plots.
            roi_item._updateHoverColor()

    def remove_rois_from_plot(self):
        """
        This function removes existing ROIs to plot new or different ones,
        or display existing ones in a different colour.
        """
        for item in self._reference_rois[
                self.widget.roi.current_tool]:
            try:
                if item.textItem:
                    self.widget.roi.plotItem.vb.removeItem(item.textItem)
                self.widget.roi.plotItem.vb.removeItem(item)
            except AttributeError:
                messagebox.show_warning.info(
                    "No (latest) ROI in device", parent=self.widget)

    def _get_value(self, proxy, prop):
        if hasattr(proxy, prop):
            return get_binding_value(getattr(proxy, prop))

    def _calculate_delta_dates(self):
        """
        Calculates the number of days between the current date and
        the date the ROI was saved.
        """
        historic_dates = self._get_value(
            self.historic_proxy.value, "date")
        self.delta_days_filtered = []
        for date in historic_dates:
            delta_time = ((datetime.datetime.now() -
                           datetime.datetime.strptime(
                date[:-7], '%Y-%m-%d %H:%M:%S')))
            delta_day = delta_time.days
            self.delta_days_filtered.append(delta_day)

    def create_lut_colors(self, color):
        ''''
        This function creates a Look-Up Table (LUT) and assigns a color
        to each ROI based on the day it was saved.
        The function normalizes the dates with the oldest saved ROI and
        then associates a color with each ROI.
        '''
        lut_colors = []
        if len(self.delta_days_filtered) > 0:
            delta_max = (np.max(self.delta_days_filtered))
            if delta_max == 0:
                delta_days_normalized = np.zeros(
                    len(self.delta_days_filtered))
            else:
                delta_days_normalized = np.array(
                    self.delta_days_filtered) / delta_max * LUT_LENGTH
            color_number = []
            lut = create_lut(color)
            for day in delta_days_normalized:
                color_number.append(int(day))
                color = [lut[int(day)][i] for i in range(3)]
                lut_colors.append(color)
        return lut_colors

    def plot_rois(self):
        number_of_rois = set([len(self.saved_rois[k])
                             for k in self.saved_rois.keys()])
        if len(number_of_rois) == 1:
            for individual_roi_info in list(zip(*self.saved_rois.values())):
                self.plotting(list(individual_roi_info))
        else:
            msg = f"Error plotting {self.remote_instance_id} historical values"
            messagebox.show_warning(
                msg, title='Error in plotting', parent=self.widget)
