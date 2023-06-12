from functools import partial

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QCheckBox, QRadioButton, QWidget


class BaseSelectionWidget(QWidget):

    changed = Signal(object)

    def __init__(self, parent=None):
        super(BaseSelectionWidget, self).__init__(parent)
        # Initialize variables
        self._motors_ids = []
        self._source_ids = []
        self._source_widgets = []
        self._current_index = 0

    def _init_source_widgets(self, as_radio_buttons=False):
        self._source_widgets.clear()
        # Initialize y_data widget
        for index, source_id in enumerate(self._source_ids):
            if as_radio_buttons:
                widget = QRadioButton(source_id, self)
            else:
                widget = QCheckBox(source_id, self)
            widget.clicked.connect(
                partial(self._source_widgets_clicked, index))
            self._source_widgets.append(widget)

    def set_motors(self, motor_ids):
        pass

    def set_sources(self, source_ids):
        pass

    def set_config(self, config):
        pass

    def get_selected_motors(self):
        pass

    def clear_all(self):
        pass

    @Slot(int)
    def _source_widgets_clicked(self, index):
        pass
