#############################################################################
# Author: <ana.garcia-tabares@xfel.eu>
# Created on April, 2022
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from enum import IntEnum

from qtpy.QtCore import Slot
from qtpy.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton)
from traits.api import Callable, Constant, Enum, List

from karabogui import icons
from karabogui.graph.common.api import BaseToolsetController, create_button

# ---------
# Play and pause class, icons and toolset
# -----------


class DisplayTool(IntEnum):
    NoTool = 0
    PlayImage = 1
    PauseImage = 2
    SendSelectCross = 3


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

    return button


class DisplayToolset(BaseToolsetController):
    tools = List([DisplayTool.PlayImage, DisplayTool.PauseImage,
                 DisplayTool.SendSelectCross])
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
    # TODO: add ui to variable names
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation Information")
        self.ok = False
        ui_annotation_text_name = QLabel('&Search by Annotation ', self)
        ui_annotation_text_name.setToolTip('Search by Annotation')
        self.ui_annotation_text = QLineEdit(self)
        ui_annotation_text_name.setBuddy(self.ui_annotation_text)

        annotation_type_name = QLabel('&Annotation Type', self)
        self.ui_annotation_type = QComboBox(self)
        self.ui_annotation_type.addItems(["Crosshair",
                                          "Rectangle"])
        annotation_type_name.setBuddy(self.ui_annotation_type)

        self.ui_keep_all = QRadioButton(
            "Keep results from previous search")
        self.ui_keep_all.setChecked(False)

        self.ui_accept_button = QPushButton('&Accept')
        self.ui_close_button = QPushButton('&Cancel')
        self.ui_accept_button.clicked.connect(self.get_annotation)
        self.ui_close_button.clicked.connect(self.close_dialog)

        main_layout = QGridLayout(self)
        main_layout.addWidget(ui_annotation_text_name, 0, 0, 1, 1)
        main_layout.addWidget(self.ui_annotation_text, 1, 0, 1, 1)
        main_layout.addWidget(annotation_type_name, 0, 1, 1, 1)
        main_layout.addWidget(self.ui_annotation_type, 1, 1, 1, 1)
        main_layout.addWidget(self.ui_keep_all, 2, 0, 1, 2)
        main_layout.addWidget(self.ui_accept_button, 3, 0)
        main_layout.addWidget(self.ui_close_button, 3, 1)

    @Slot()
    def close_dialog(self):
        self.close()
        self.ok = False

    @Slot()
    def get_annotation(self):
        self.ui_annotation_value = self.ui_annotation_text.text()
        self.ui_annotation_type_value = self.ui_annotation_type.currentText()
        self.ok = True
        self.accept()
