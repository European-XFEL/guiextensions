#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from enum import IntEnum

from qtpy.QtCore import QDate, Slot
from qtpy.QtWidgets import (
    QComboBox, QDateTimeEdit, QDialog, QGridLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton)
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation Information")
        annotation_text_name = QLabel('&Search by Annotation ', self)
        annotation_text_name.setToolTip('Search by Annotation')
        self.annotation_text = QLineEdit(self)
        annotation_text_name.setBuddy(self.annotation_text)

        annotation_type_name = QLabel('&Annotation Type', self)
        self.annotation_type = QComboBox(self)
        self.annotation_type.addItems(["Crosshair",
                                       "Rect"])
        annotation_type_name.setBuddy(self.annotation_type)

        self.keep_all = QRadioButton(
            "Keep results from previous search")
        self.keep_all.setChecked(False)

        self.accept_button = QPushButton('&Get Data')
        self.plot_button = QPushButton('&Plot')
        self.close_button = QPushButton('&Close')
        self.close_button.clicked.connect(self.close_dialog)

        # start_time Calendar Widget
        start_time_label = QLabel('Start Date', self)
        self.start_time = QDateTimeEdit()
        self.start_time.setDate(QDate.currentDate().addDays(-MAX_DAYS*2))
        self.start_time.setCalendarPopup(True)
        self.start_time.setDisplayFormat("dd.MM.yyyy")
        self.start_time.setObjectName("start_time")
        # end_time Calendar Widget
        end_time_label = QLabel('End Date', self)
        self.end_time = QDateTimeEdit()
        self.end_time.setDate(QDate.currentDate().addDays(1))
        self.end_time.setCalendarPopup(True)
        self.end_time.setDisplayFormat("dd.MM.yyyy")
        self.end_time.setObjectName("end_time")

        main_layout = QGridLayout(self)
        main_layout.addWidget(annotation_text_name, 0, 0, 1, 1)
        main_layout.addWidget(self.annotation_text, 1, 0, 1, 1)
        main_layout.addWidget(annotation_type_name, 0, 1, 1, 1)
        main_layout.addWidget(self.annotation_type, 1, 1, 1, 1)
        main_layout.addWidget(self.keep_all, 2, 0, 1, 2)
        main_layout.addWidget(self.accept_button, 3, 0)
        main_layout.addWidget(self.plot_button, 3, 1)

        # Add connections to calendar
        main_layout.addWidget(start_time_label, 4, 0)
        main_layout.addWidget(self.start_time, 5, 0)
        main_layout.addWidget(end_time_label, 4, 1)
        main_layout.addWidget(self.end_time, 5, 1)

    @Slot()
    def close_dialog(self):
        self.close()
