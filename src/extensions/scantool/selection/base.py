from functools import partial

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QCheckBox, QWidget

from ..const import MOTOR_NAMES, SOURCE_NAMES


class BaseSelectionWidget(QWidget):

    changed = Signal(object)

    def __init__(self, parent=None):
        super(BaseSelectionWidget, self).__init__(parent)
        self._checkboxes = []

        # Initialize variables
        self._motors = MOTOR_NAMES
        self._sources = SOURCE_NAMES
        self._motors_ids = []
        self._source_ids = []
        self._checkboxes = []
        self._current_index = 0

    def _init_checkboxes(self):
        # Initialize y_data widget
        for index, device in enumerate(self._sources):
            checkbox = QCheckBox(device, self)
            checkbox.clicked.connect(partial(self._checkboxes_clicked, index))
            self._checkboxes.append(checkbox)
        return self._checkboxes

    def set_motors(self, motors, motor_ids):
        pass

    def set_sources(self, sources, source_ids):
        # Setup needed checkboxes from already existing
        for index, device in enumerate(source_ids):
            checkbox = self._checkboxes[index]
            checkbox.setText(device)
            checkbox.setVisible(True)

        # Then hide unused checkboxes
        for checkbox in self._checkboxes[len(sources):]:
            checkbox.setVisible(False)

        self._sources = sources
        self._source_ids = source_ids

    def set_config(self, config):
        pass

    @Slot(int)
    def _checkboxes_clicked(self, index):
        pass
