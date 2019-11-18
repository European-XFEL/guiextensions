from functools import partial

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QCheckBox, QWidget

from ..const import MOTOR_NAMES, SOURCE_NAMES


class BaseSelectionWidget(QWidget):

    changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super(BaseSelectionWidget, self).__init__(parent)
        self._checkboxes = []

        # Initialize variables
        self._motors = MOTOR_NAMES
        self._sources = SOURCE_NAMES
        self._checkboxes = []
        self._current_index = 0

    def _init_checkboxes(self):
        # Initialize y_data widget
        for index, device in enumerate(self._sources):
            checkbox = QCheckBox(device, self)
            checkbox.clicked.connect(partial(self._checkboxes_clicked, index))
            self._checkboxes.append(checkbox)

        return self._checkboxes

    def set_motors(self, motors):
        pass

    def set_sources(self, sources):
        # Setup needed checkboxes from already existing
        for index, device in enumerate(sources):
            checkbox = self._checkboxes[index]
            checkbox.setText(device)
            checkbox.setVisible(True)

        # Then hide unused checkboxes
        for checkbox in self._checkboxes[len(sources):]:
            checkbox.setVisible(False)

        self._sources = sources

    def set_config(self, config):
        pass

    @pyqtSlot(int)
    def _checkboxes_clicked(self, index):
        pass
