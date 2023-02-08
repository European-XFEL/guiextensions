from functools import partial

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QCheckBox, QRadioButton, QWidget

from ..const import MOTOR_NAMES, SOURCE_NAMES


class BaseSelectionWidget(QWidget):

    changed = Signal(object)

    def __init__(self, parent=None):
        super(BaseSelectionWidget, self).__init__(parent)
        # Initialize variables
        self._motors = MOTOR_NAMES
        self._sources = SOURCE_NAMES
        self._motors_ids = []
        self._source_ids = []
        self._source_widgets = []
        self._current_index = 0

    def _init_source_widgets(self, as_radio_buttons=False):
        # Initialize y_data widget
        for index, device in enumerate(self._sources):
            if as_radio_buttons:
                widget = QRadioButton(device, self)
            else:
                widget = QCheckBox(device, self)
            widget.clicked.connect(
                partial(self._source_widgets_clicked, index))
            self._source_widgets.append(widget)

    def set_motors(self, motors, motor_ids):
        pass

    def set_sources(self, sources, source_ids):
        # Setup needed checkboxes from already existing
        for index, device in enumerate(source_ids):
            checkbox = self._source_widgets[index]
            checkbox.setText(device)
            checkbox.setVisible(True)

        # Then hide unused checkboxes
        for checkbox in self._source_widgets[len(sources):]:
            checkbox.setVisible(False)

        self._sources = sources
        self._source_ids = source_ids

    def set_config(self, config):
        pass

    def get_selected_motors(self):
        pass

    @Slot(int)
    def _source_widgets_clicked(self, index):
        pass
