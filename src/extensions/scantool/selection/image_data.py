import os

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QButtonGroup

from karabogui.util import SignalBlocker

from .base import BaseSelectionWidget
from ..const import ADD, REMOVE, X_DATA, Y_DATA, Z_DATA


class ImageDataSelectionWidget(BaseSelectionWidget):

    def __init__(self, parent=None):
        super(ImageDataSelectionWidget, self).__init__(parent)
        ui_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               'image_data.ui')
        uic.loadUi(ui_path, self)

        button_group = QButtonGroup(parent)
        button_group.setExclusive(True)
        checkboxes = self._init_checkboxes()
        for checkbox in checkboxes:
            self.z_groupbox.layout().addWidget(checkbox)
            button_group.addButton(checkbox)

        # Initialize axes data
        self.ui_x_combobox.addItems(self._motors)
        self.ui_y_combobox.addItems(self._motors)
        self.ui_y_combobox.setCurrentIndex(1)

        self.ui_x_combobox.currentIndexChanged.connect(self._x_axis_changed)
        self.ui_y_combobox.currentIndexChanged.connect(self._y_axis_changed)

    # ---------------------------------------------------------------------
    # Public methods

    def set_motors(self, motors):
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.clear()
            self.ui_x_combobox.addItems(motors)

        with SignalBlocker(self.ui_y_combobox):
            self.ui_y_combobox.clear()
            self.ui_y_combobox.addItems(motors)
            self.ui_y_combobox.setCurrentIndex(1)

        self._motors = motors

    def set_config(self, config):
        # 1. Images only have one config
        config = config[0]

        # 2. Setup widgets to indicate current config
        x_index = self._motors.index(config[X_DATA])
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.setCurrentIndex(x_index)

        y_index = self._motors.index(config[Y_DATA])
        with SignalBlocker(self.ui_y_combobox):
            self.ui_y_combobox.setCurrentIndex(y_index)

        for index, checkbox in enumerate(self._checkboxes):
            checked = checkbox.text() == config[Z_DATA]
            checkbox.setChecked(checked)
            if checked:
                self._current_index = index

    # ---------------------------------------------------------------------
    # Qt slots

    @pyqtSlot(int, bool)
    def _checkboxes_clicked(self, index):
        # Do not do anything if same index is clicked
        if index == self._current_index:
            return

        x_data = self._motors[self.ui_x_combobox.currentIndex()]
        y_data = self._motors[self.ui_y_combobox.currentIndex()]

        removed = [{X_DATA: x_data,
                    Y_DATA: y_data,
                    Z_DATA: self._sources[self._current_index]}]

        added = [{X_DATA: x_data,
                  Y_DATA: y_data,
                  Z_DATA: self._sources[index]}]

        self._current_index = index
        self.changed.emit({REMOVE: removed, ADD: added})

    @pyqtSlot(int)
    def _x_axis_changed(self, x_index):
        """Changes for the x- and y-axis are coupled, and this method contains
           the logic for both changes."""

        y_index = int(not x_index)
        with SignalBlocker(self.ui_y_combobox):
            self.ui_y_combobox.setCurrentIndex(y_index)

        x_data = self._motors[x_index]
        y_data = self._motors[y_index]
        z_data = self._sources[self._current_index]

        removed = [{X_DATA: y_data, Y_DATA: x_data, Z_DATA: z_data}]
        added = [{X_DATA: x_data, Y_DATA: y_data, Z_DATA: z_data}]

        self.changed.emit({REMOVE: removed, ADD: added})

    @pyqtSlot(int)
    def _y_axis_changed(self, index):
        """Changes for the x- and y-axis are coupled, so when the y-axis is
           changed, we just change the x-axis and let the logic there dictate
           our fate."""

        self.ui_x_combobox.setCurrentIndex(int(not index))
