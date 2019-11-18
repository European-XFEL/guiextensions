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

        # Initialize x_data
        self.ui_x_combobox.addItems(self._motors)
        self.ui_y_combobox.addItems(self._motors)
        self.ui_y_combobox.setCurrentIndex(1)

        # # Disable selection on default x_data
        self.ui_x_combobox.setDisabled(True)
        self.ui_y_combobox.setDisabled(True)

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
