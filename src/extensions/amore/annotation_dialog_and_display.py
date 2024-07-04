#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
import os
from enum import IntEnum

from qtpy import uic
from qtpy.QtCore import QDate, Slot
from qtpy.QtWidgets import QDialog
from traits.api import Callable, Constant, Enum, List

from karabogui import icons
from karabogui.graph.common.api import BaseToolsetController, create_button

# ---------
# Play and pause class, icons and toolset
# -----------
MAX_DAYS = 2.5


class DisplayTool(IntEnum):
    NoTool = 0
    PlayImage = 1
    PauseImage = 2
    SendSelectCross = 3
    DisplayInterval = 4


def display_factory(tool):
    button = None
    if tool is DisplayTool.PlayImage:
        button = create_button(icon=icons.mediaStart,
                               checkable=True,
                               tooltip="Start image display")

    if tool is DisplayTool.PauseImage:
        button = create_button(icon=icons.mediaPause,
                               checkable=True,
                               tooltip="Pause image display")

    if tool is DisplayTool.SendSelectCross:
        button = create_button(icon=icons.arrowFancyRight,
                               checkable=True,
                               tooltip="Send selected ROI "
                               "coordinates to Device")

    if tool is DisplayTool.DisplayInterval:
        button = create_button(icon=icons.arrowFancyLeft,
                               checkable=True,
                               tooltip="Get ROIs (Rect and Cross)"
                                       "from a given time interval")

    return button


class DisplayToolset(BaseToolsetController):
    tools = List([DisplayTool.PlayImage, DisplayTool.PauseImage,
                 DisplayTool.SendSelectCross, DisplayTool.DisplayInterval])
    factory = Callable(display_factory)
    current_tool = Enum(*DisplayTool)
    default_tool = Constant(DisplayTool.NoTool)

    def select(self, tool):
        """Sets the selected mouse mode and uncheck any previously tool"""

        # Uncheck current tool, if there is a button for it
        if self.current_tool in self.buttons:
            self.buttons[
                self.current_tool].setChecked(False)

        # if non of the buttons are checked, revert to the default tool
        if all(not button.isChecked() for button in self.buttons.values()):
            tool = self.default_tool

        super(DisplayToolset, self).select(tool)


class AnnotationSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        super(AnnotationSearchDialog, self).__init__(parent)
        ui_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               'annotation.ui')
        uic.loadUi(ui_path, self)

        self.annotation_type.addItems(["Crosshair",
                                       "Rect"])
        self.start_time.setDate(QDate.currentDate().addDays(-int(MAX_DAYS*2)))
        self.start_time.setCalendarPopup(True)
        self.start_time.setDisplayFormat("dd.MM.yyyy")
        self.start_time.setObjectName("start_time")
        self.end_time.setDate(QDate.currentDate().addDays(1))
        self.end_time.setCalendarPopup(True)
        self.end_time.setDisplayFormat("dd.MM.yyyy")
        self.end_time.setObjectName("end_time")

    @Slot()
    def close_dialog(self):
        self.close()
