from qtpy.QtWidgets import QWidget
from traits.api import Event, HasStrictTraits, Instance

from ..selection.image_data import ImageDataSelectionWidget
from ..selection.xy_data import XYDataSelectionWidget
from ..widget import get_container


class DataSelectionController(HasStrictTraits):

    widget = Instance(QWidget)
    changed = Event

    _selection_widget = Instance(QWidget)

    def __init__(self, parent=None):
        super(DataSelectionController, self).__init__()
        self.widget = get_container(parent)
        self.widget.setFixedWidth(250)

    # ---------------------------------------------------------------------
    # Public methods

    def use_xy_selection(self):
        self._use_selection(XYDataSelectionWidget)

    def use_image_selection(self):
        self._use_selection(ImageDataSelectionWidget)

    def set_devices(self, motor_ids, source_ids):
        if self._selection_widget is None:
            return

        # Bookkeep the changes in the selection such that it is persistent
        # on the next scans (with the same config

        self._selection_widget.set_motors(motor_ids)
        self._selection_widget.set_sources(source_ids)

    def set_config(self, config):
        if self._selection_widget is None:
            return

        self._selection_widget.set_config(config)

    def get_selected_motors(self):
        return self._selection_widget.get_selected_motors()

    def aligner_results_enabled(self):
        return self._selection_widget.are_aligner_results_enabled()

    def set_clear_button_enabled(self, state):
        if isinstance(self._selection_widget, XYDataSelectionWidget):
            # 2D plot do not have clear_button
            self._selection_widget.clear_button.setEnabled(state)

    # ---------------------------------------------------------------------
    # Private methods

    def _use_selection(self, klass):
        """Generic class to remove and destroy existing widget and
           instantiate the requested widget to the base widget layout."""

        # Do something only if request is different from current widget
        if not isinstance(self._selection_widget, klass):
            # Remove unwanted widget
            if self._selection_widget is not None:
                self.widget.remove_widget(self._selection_widget)
                self._selection_widget.setParent(None)
                self._selection_widget.changed.disconnect()
                self._selection_widget.destroy()

            # Instantiate requested widget
            self._selection_widget = klass(parent=self.widget)
            self._selection_widget.changed.connect(self._change)
            self.widget.add_widget(self._selection_widget)

        return self._selection_widget

    # ---------------------------------------------------------------------
    # Qt slots

    def _change(self, changes):
        self.changed = changes

    def clear(self):
        self._selection_widget.clear_all()
