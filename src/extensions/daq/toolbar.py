#############################################################################
# Author: <dennis.goeries@xfel.eu>
# This file is part of the Karabo Gui.
#
# http://www.karabo.eu
#
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#
# The Karabo Gui is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 3 or higher.
#
# You should have received a copy of the General Public License, version 3,
# along with the Karabo Gui.
# If not, see <https://www.gnu.org/licenses/gpl-3.0>.
#
# The Karabo Gui is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
#############################################################################
import weakref

from qtpy import uic
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget

from karabogui.api import wait_cursor

from .utils import get_panel_ui

_QEDIT_STYLE = """
QLineEdit {{
    border: 1px solid gray;
    border-radius: 2px;
    background-color: rgba{};
}}
QLineEdit:focus
{{
    border: 1px solid rgb(48,140,198);
}}
"""

_CHANGED_COLOR = (0, 170, 255, 128)


class SearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        uic.loadUi(get_panel_ui("group_filter.ui"), self)
        self.tree_view = None

        self.ui_filter.returnPressed.connect(self._search_clicked)
        self.ui_filter.textChanged.connect(self._filter_modified)
        self.ui_search.clicked.connect(self._search_clicked)
        self.ui_clear.clicked.connect(self._clear_clicked)
        # Set StyleSheets
        self._filter_normal = _QEDIT_STYLE.format((255, 255, 255, 255))
        self._filter_changed = _QEDIT_STYLE.format(_CHANGED_COLOR)
        self.ui_filter.setStyleSheet(self._filter_normal)
        self._enable_filter(True)

    # -----------------------------------------
    # Qt Slots

    def _enable_filter(self, enable=False):
        self.ui_filter.setText("")
        self.ui_filter.setPlaceholderText("")
        self.ui_filter.setEnabled(enable)
        self.ui_search.setEnabled(enable)
        self.ui_clear.setEnabled(enable)

    def _set_filter_modified(self, modified):
        sheet = self._filter_changed if modified else self._filter_normal
        self.ui_filter.setStyleSheet(sheet)

    # -----------------------------------------
    # Public interface

    def setView(self, view):
        self.tree_view = weakref.ref(view)

    # -----------------------------------------
    # Qt Slots

    @Slot()
    def _filter_modified(self):
        self._set_filter_modified(True)

    @Slot()
    def _search_clicked(self):
        with wait_cursor():
            pattern = str(self.ui_filter.text())
            self.ui_filter.setPlaceholderText(pattern)

            # View and activate
            tree_view = self.tree_view()
            tree_view.expandAll()
            proxy_model = tree_view.model()
            proxy_model.setFilterFixedString(pattern)
            self._set_filter_modified(False)

    @Slot()
    def _clear_clicked(self):
        with wait_cursor():
            pattern = ''
            self.ui_filter.setText(pattern)
            self.ui_filter.setPlaceholderText(pattern)

            # View and activate
            tree_view = self.tree_view()
            tree_view.collapseAll()
            proxy_model = tree_view.model()
            proxy_model.setFilterFixedString(pattern)
            self._set_filter_modified(False)
