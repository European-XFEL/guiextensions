#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from collections import OrderedDict, defaultdict
from functools import partial

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
from .aux_filtering_and_plotting import display_saved_data
from .constants_keys import (
    HISTORY_HASH_PROPERTIES, HISTORY_HASH_TYPES, TOOL_MAP)
from .displaying_from_past import IntervalSettings
from .roi_annotator import RoiAnnotator
from .roi_requestor import RoiRequestor

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
    coordinatesTool = Instance(IntervalSettings, args=())
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

    # Related to the device used to saved the coordinates
    proxy_dictionary = OrderedDict()
    proxy_dictionary_history = OrderedDict()
    # The remote_instance_id of the roi proxy
    remote_instance_id = String()
    # The roi proxy node holding the roi information
    roi_proxy = Instance(PropertyProxy)
    historic_proxy = Instance(PropertyProxy)

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

        # we delegate the sending rois to device to the RoiAnnotator,
        # which can interact via slots witht the rest of the system
        self._roi_annotator = RoiAnnotator(self, parent=parent)
        # we delegate the request ROIS from interval to the
        # RoiRequestor
        self._roi_requestor = RoiRequestor(self, parent=parent)
        # Adding calendar to Layout
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
        else:
            self.remote_instance_id = proxy.root_proxy.device_id
        # If a device is offline, we still add it.
        return True

    def binding_update(self, proxy):
        if self.roi_proxy is None:
            self.add_proxy(proxy)
        if self.historic_proxy is None:
            self.add_proxy(proxy)

    def value_update(self, proxy):
        if proxy is self.roi_proxy:
            # We plot current roi information from remote proxy
            # No need to show the error message
            # if there is no a value in the device
            self.update_from_remote(False)
            # If its a bit hard to add a new value from device
            # Either we don't allow to change the ROI
            # or we desactivate this
            # pass
        elif proxy is self.historic_proxy:
            # we have to plot historic data delivered on remote proxy
            # This could be a bit confussin, specially if we mix
            # crosses and rectangles
            # We only update when we have new values
            # and the user has requested the past values
            pass
        else:
            # self.proxy updates the image
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
            # Send selected cross to the ROIAnnotation device
            # We have to know what roi is currently selected
            selected_roi = self.widget.roi._current_item[
                self.widget.roi.current_tool]
            # If they try to send nothing to the device
            # we don't do anything
            if selected_roi:
                if (selected_roi not in
                        self._reference_rois[self.widget.roi.current_tool]):
                    self._roi_annotator.send_selected_coordinates(selected_roi)
                else:
                    messagebox.show_alarm(
                        "ROI already saved, "
                        "please select a ROI before sending it to the device.",
                        parent=self.widget)
            else:
                messagebox.show_alarm(
                    "Nothing selected, "
                    "please select a ROI before sending it to the device.",
                    parent=self.widget)
            self._display_toolset.select(
                DisplayTool.NoTool)
        elif display_tool is DisplayTool.NoTool:
            # reset the mouse mode to whatever it was before
            self._viewbox.set_mouse_mode(self._mouse_mode)

    def state_update(self, proxy):
        state = self._get_state(proxy)
        # Normally, the state should not be None
        if State(state) is State.RUNNING:
            self._pause_image = False

    def _get_state(self, proxy):
        root_proxy = proxy.root_proxy
        state = get_binding_value(root_proxy.state_binding)
        return state

    def plot(self):
        return self._plot

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

    def update_from_remote(self, flag=True):
        color = INDIVIDUAL_ROI_COLOR
        info = []
        if (self.roi_proxy is None and flag):
            self.no_rois_found_message(
                f"Device {self.remote_instance_id} not instantiated")
            return
        for prop, prop_type in zip(HISTORY_HASH_PROPERTIES,
                                   HISTORY_HASH_TYPES):
            prop_value = self._get_value(self.roi_proxy.value,
                                         prop)
            # There are values in the node with the correct type
            if (prop_value is not None and (type(prop_value) == prop_type)):
                info.append(
                    self._get_value(self.roi_proxy.value,
                                    prop))
            # There are values in the node property but the wrong type
            elif type(prop_value) == prop_type:
                messagebox.show_error(
                    f"Wrong data type for {prop}", parent=self.widget)
                return
            # There are no values and we want to make the user aware of this
            elif (prop_value is None and flag):
                # We show a message in case someone wants
                # to plot/display the latest value sent to device
                # but there's nothing there
                self.no_rois_found_message(
                    "Last value sent to device cannot be "
                    "plotted. Please, get values from "
                    "interval.")
                return

        info.append(color)
        self.widget.roi.selected.emit(ROITool.NoROI)
        self.widget.roi.selected.emit(
            self._get_value(self.roi_proxy.value,
                            "roiTool"))
        self.plotting(info)

    def no_rois_found_message(self, s):
        # If there's not ROI that matches the search then
        # we show a message, to make sure the users now there's
        # somethin running.
        messagebox.show_warning(
            s, title='No ROIs in Device', parent=self.widget)

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
        # ROIs can't be removed to avoid possible misunderstandings
        # since in fact they can only be hidden from plot but
        # not from history.
        roi_item.translatable = False
        # Connect some signals
        # The standard signals that are normally connected
        # by the standard add function
        # + the sigHoverEvent that shows when the data was saved.
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
        # Bookkeeping. Add the items to the list of existing ROI tools
        self.widget.roi._rois[tool].append(roi_item)
        self._reference_rois[tool].append(roi_item)

        # Add the ROI item to the plot
        self.widget.roi._add_to_plot(roi_item, ignore_bounds)

        if current_item:
            self.widget.roi._current_tool = tool
            self.widget.roi._set_current_item(roi_item, update=False)
            # Set as current item, in which affects the aux plots.
            roi_item._updateHoverColor()
        # return roi_item

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
                messagebox.show_warning.info("No (latest) ROI in device")

    def _get_value(self, proxy, prop):
        if hasattr(proxy, prop):
            return get_binding_value(getattr(proxy, prop))
