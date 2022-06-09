import os

from qtpy import uic
from qtpy.QtCore import Slot

from karabogui.util import SignalBlocker

from ..const import ADD, MOTOR_NAMES, REMOVE, X_DATA, Y_DATA
from .base import BaseSelectionWidget


class XYDataSelectionWidget(BaseSelectionWidget):

    def __init__(self, parent=None):
        super(XYDataSelectionWidget, self).__init__(parent)
        ui_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               'xy_data.ui')
        uic.loadUi(ui_path, self)

        checkboxes = self._init_checkboxes()
        for checkbox in checkboxes:
            self.y_groupbox.layout().addWidget(checkbox)

        # Disable selection on default x_data
        self.ui_x_combobox.addItems(MOTOR_NAMES)
        self.ui_x_combobox.currentIndexChanged.connect(self._x_axis_changed)

    # ---------------------------------------------------------------------
    # Public methods

    def set_motors(self, motors, motor_ids):
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.clear()
            self.ui_x_combobox.addItems(motor_ids)

        self._motors = motors
        self._motor_ids = motor_ids

    def set_config(self, config):
        # 1. Collapse to unique device names
        x_data = set()
        y_data = set()

        for conf in config:
            x_data.add(conf[X_DATA])
            y_data.add(conf[Y_DATA])

        # 2. Check if x_data is not unique
        if len(x_data) != 1:
            return

        # 3. Setup widgets to indicate current config
        x_index = self._motor_ids.index(next(iter(x_data)))
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.setCurrentIndex(x_index)
            self._current_index = x_index

        for checkbox in self._checkboxes:
            checkbox.setChecked(checkbox.text() in y_data)

    # ---------------------------------------------------------------------
    # Qt slots

    @Slot(int, bool)
    def _checkboxes_clicked(self, index):
        checked = [checkbox.isChecked() for checkbox in
                   self._checkboxes[:len(self._sources)]]
        if not any(checked):
            self._checkboxes[index].setChecked(True)
            return

        changes = ADD if self._checkboxes[index].isChecked() else REMOVE
        x_data = self._motor_ids[self.ui_x_combobox.currentIndex()]
        y_data = self._source_ids[index]
        self.changed.emit({changes: [{X_DATA: x_data, Y_DATA: y_data}]})

    @Slot(int)
    def _x_axis_changed(self, index):
        # 1. Get relevant values
        x_current = self._motor_ids[self._current_index]
        x_data = self._motor_ids[index]
        y_data_list = self._get_all_y_data()

        # 2. Get to-remove configs
        removed = []
        for y_data in y_data_list:
            removed.append({X_DATA: x_current, Y_DATA: y_data})

        # 3. Get to-add configs
        added = []
        for y_data in y_data_list:
            added.append({X_DATA: x_data, Y_DATA: y_data})

        # 5. Finalize changes
        self._current_index = index
        self.changed.emit({REMOVE: removed, ADD: added})

    # ---------------------------------------------------------------------
    # Private methods

    def _get_all_y_data(self):
        y_data = []
        for index, source in enumerate(self._source_ids):
            if self._checkboxes[index].isChecked():
                y_data.append(source)
        return y_data
