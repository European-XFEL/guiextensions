from qtpy import uic
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QDialog

from karabo.native import create_html_hash
from karabogui.api import icons

from .utils import get_config_changes, get_dialog_ui


class MotorConfigurationPreview(QDialog):

    def __init__(self, old, new, terminal, stage, parent=None):
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(False)
        ui_file = get_dialog_ui("motor_stage_configuration_preview.ui")
        uic.loadUi(ui_file, self)
        flags = Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(self.windowFlags() | flags)
        self.setWindowTitle("Motor Configuration Comparison")

        text = ("View existing and proposed configuration for device "
                f"<b>{terminal}</b> with QR Code Stage <b>{stage}</b>.")
        self.info_label.setText(text)

        self._show_changes = False
        self.swap_button.setIcon(icons.change)
        self.swap_button.clicked.connect(self._swap_view)
        # Changes between each configuration
        changes_a, changes_b = get_config_changes(old, new)
        html_a = self._get_html_configuration(changes_a)
        html_b = self._get_html_configuration(changes_b)
        self.existing_changes_view.setHtml(html_a)
        self.new_changes_view.setHtml(html_b)

        # New Configuration
        html = create_html_hash(new, include_attributes=False)
        self.configuration_view.setHtml(html)

    def _get_html_configuration(self, config):
        """Provide the html view of a `config` hash"""
        if config.empty():
            return "<center>No changes in configuration</center>"

        return create_html_hash(config, include_attributes=False)

    # ---------------------------------------------------------------------
    # Slot Interface

    @Slot()
    def _swap_view(self):
        self._show_changes = not self._show_changes
        text = "Show Configuration" if self._show_changes else "Show Changes"
        self.swap_button.setText(text)
        self.stack_widget.setCurrentIndex(int(self._show_changes))
        text = "Changes" if self._show_changes else "Retrieved Configuration"
        self.show_label.setText(text)
