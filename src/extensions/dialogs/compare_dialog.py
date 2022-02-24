#############################################################################
# Author_layout: <dennis.goeries@xfel.eu>
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from qtpy import uic
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget)

from karabo.native import Hash, create_html_hash

from .utils import get_dialog_ui

EMPTY_CHANGES = Hash("None -", "No critical changes")


class Page(QWidget):
    def __init__(self, title, data, parent=None):
        super().__init__(parent=parent)
        widget_title = QLabel(title, parent=self)
        if data.empty():
            old = EMPTY_CHANGES
            new = EMPTY_CHANGES
        else:
            old = data["old"]
            new = data["new"]

        old_layout = QVBoxLayout()
        old_layout.setContentsMargins(0, 0, 0, 0)
        old_data = QTextEdit(self)
        old_data.setHtml(create_html_hash(old))
        old_data.setReadOnly(True)
        old_layout.addWidget(QLabel("<b>Old Configuration - Properties</b>"))
        old_layout.addWidget(old_data)

        new_layout = QVBoxLayout()
        new_layout.setContentsMargins(0, 0, 0, 0)

        new_data = QTextEdit(self)
        new_data.setHtml(create_html_hash(new))
        new_layout.addWidget(QLabel("<b>New Configuration - Properties</b>"))
        new_layout.addWidget(new_data)

        # Build up the page
        hor_layout = QHBoxLayout()
        hor_layout.setContentsMargins(0, 0, 0, 0)
        hor_layout.addLayout(old_layout)
        hor_layout.addLayout(new_layout)

        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.addWidget(widget_title)
        spacer = QLabel()
        spacer.setMinimumHeight(10)
        widget_layout.addWidget(spacer)
        widget_layout.addLayout(hor_layout)
        self.setLayout(widget_layout)


class CompareDialog(QDialog):

    def __init__(self, title, data, parent=None):
        super().__init__(parent=parent)
        uic.loadUi(get_dialog_ui("comparison_dialog.ui"), self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.ui_title.setText(title)
        for deviceId, config in data.items():
            title = ("Configuration changes of critical properties of "
                     f"<b>{deviceId}</b>")
            page = Page(title, config, parent=self)
            self.ui_stack_widget.addWidget(page)
