import os

from qtpy import uic
from qtpy.QtCore import Slot

from karabogui.util import SignalBlocker

from ..const import ADD, ALIGNER, REMOVE, REMOVE_ALL, X_DATA, Y_DATA
from .base import BaseSelectionWidget


class XYDataSelectionWidget(BaseSelectionWidget):

    def __init__(self, parent=None):
        super(XYDataSelectionWidget, self).__init__(parent)
        ui_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               'xy_data.ui')
        uic.loadUi(ui_path, self)

        self.ui_x_combobox.currentIndexChanged.connect(self._x_axis_changed)
        self.aligner_cbox.clicked.connect(
            self._show_aligner_results_clicked)
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self._clear_all_clicked)

    # ---------------------------------------------------------------------
    # Public methods

    def set_motors(self, motor_ids):
        # Remove duplicates if several scans are plotted
        motor_ids = list(dict.fromkeys(motor_ids))
        with SignalBlocker(self.ui_x_combobox):
            self.ui_x_combobox.clear()
            self.ui_x_combobox.addItems(motor_ids)
        self._motor_ids = motor_ids

    def set_sources(self, source_ids):
        self._source_ids = source_ids

        # Remove existing checkboxes
        for i in reversed(range(self.y_groupbox.layout().count())):
            self.y_groupbox.layout().itemAt(i).widget().close()
            self.y_groupbox.layout().takeAt(i)

        self._init_source_widgets()
        for checkbox in self._source_widgets:
            checkbox.setChecked(True)
            self.y_groupbox.layout().addWidget(checkbox)
        self.clear_button.setEnabled(True)

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

        for checkbox in self._source_widgets:
            checkbox.setChecked(checkbox.text() in y_data)

    def get_selected_motors(self):
        return [self.ui_x_combobox.currentText()]

    def are_aligner_results_enabled(self):
        return self.aligner_cbox.isChecked()

    # ---------------------------------------------------------------------
    # Qt slots

    @Slot()
    def _show_aligner_results_clicked(self):
        self._emit_changes()

    @Slot(int, bool)
    def _source_widgets_clicked(self, index):
        checked = [checkbox.isChecked() for checkbox in self._source_widgets]
        if not any(checked):
            self._source_widgets[index].setChecked(True)
            return

        self._emit_changes()

    @Slot(int)
    def _x_axis_changed(self, index):
        self._emit_changes()

    def _emit_changes(self):
        # Remove all configs and add selected motors and sources
        removed = []
        added = []

        for motor_index, motor_id in enumerate(self._motor_ids):
            for source_index, source_id in enumerate(self._source_ids):
                removed.append({X_DATA: motor_id, Y_DATA: source_id})
                if (self.ui_x_combobox.currentIndex() == motor_index
                   and self._source_widgets[source_index].isChecked()):
                    added.append({X_DATA: motor_id, Y_DATA: source_id})

        # Emit config
        self.changed.emit({REMOVE: removed, ADD: added,
                           ALIGNER: self.aligner_cbox.isChecked()})

    @Slot()
    def _clear_all_clicked(self):
        self.clear_all()
        self.clear_button.setEnabled(False)

    def clear_all(self):
        self.changed.emit({REMOVE_ALL: True})

        self._motor_ids.clear()
        self._source_ids.clear()

        # Clear motor checkbox
        self.ui_x_combobox.clear()

        # Remove existing checkboxes
        for i in reversed(range(self.y_groupbox.layout().count())):
            self.y_groupbox.layout().itemAt(i).widget().close()
            self.y_groupbox.layout().takeAt(i)
