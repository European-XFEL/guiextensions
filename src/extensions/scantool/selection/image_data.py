import os

from qtpy import uic
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QButtonGroup

from karabogui.util import SignalBlocker

from ..const import ADD, ALIGNER, REMOVE, X_DATA, Y_DATA, Z_DATA
from .base import BaseSelectionWidget


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
        self.aligner_cbox.clicked.connect(
            self._show_aligner_results_clicked)

    # ---------------------------------------------------------------------
    # Public methods

    def set_motors(self, motors, motor_ids):
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.clear()
            self.ui_x_combobox.addItems(motor_ids)

        with SignalBlocker(self.ui_y_combobox):
            self.ui_y_combobox.clear()
            self.ui_y_combobox.addItems(motor_ids)
            self.ui_y_combobox.setCurrentIndex(1)

        self._motors = motors
        self._motor_ids = motor_ids

    def set_config(self, config):
        # 1. Images only have one config
        config = config[0]

        # 2. Setup widgets to indicate current config
        x_index = self._motor_ids.index(config[X_DATA])
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.setCurrentIndex(x_index)

        y_index = self._motor_ids.index(config[Y_DATA])
        with SignalBlocker(self.ui_y_combobox):
            self.ui_y_combobox.setCurrentIndex(y_index)

        for index, checkbox in enumerate(self._checkboxes):
            checked = checkbox.text() == config[Z_DATA]
            checkbox.setChecked(checked)
            if checked:
                self._current_index = index

    def get_selected_motors(self):
        return [self.ui_x_combobox.currentText(),
                self.ui_y_combobox.currentText()]

    def are_aligner_results_enabled(self):
        return self.aligner_cbox.isChecked()

    # ---------------------------------------------------------------------
    # Qt slots

    @Slot(int, bool)
    def _checkboxes_clicked(self, index):
        # Do not do anything if same index is clicked
        if index == self._current_index:
            return

        self._current_index = index
        self._emit_changes()

    @Slot(int)
    def _x_axis_changed(self, x_index):
        """Changes for the x- and y-axis are coupled, and this method contains
           the logic for both changes."""

        y_index = int(not x_index)
        with SignalBlocker(self.ui_y_combobox):
            self.ui_y_combobox.setCurrentIndex(y_index)

        self._emit_changes()

    @Slot(int)
    def _y_axis_changed(self, index):
        """Changes for the x- and y-axis are coupled, so when the y-axis is
           changed, we just change the x-axis and let the logic there dictate
           our fate."""
        self.ui_x_combobox.setCurrentIndex(int(not index))
        self._emit_changes()

    @Slot()
    def _show_aligner_results_clicked(self):
        self._emit_changes()

    def _emit_changes(self):
        x_data = self._motor_ids[self.ui_x_combobox.currentIndex()]
        y_data = self._motor_ids[self.ui_y_combobox.currentIndex()]
        z_data = self._source_ids[self._current_index]

        removed = [{X_DATA: y_data, Y_DATA: x_data, Z_DATA: z_data}]
        added = [{X_DATA: x_data, Y_DATA: y_data, Z_DATA: z_data}]

        # Emit config
        self.changed.emit({REMOVE: removed, ADD: added,
                           ALIGNER: self.aligner_cbox.isChecked()})
