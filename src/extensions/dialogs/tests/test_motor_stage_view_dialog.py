from qtpy.QtCore import Qt

from extensions.dialogs.api import MotorConfigurationPreview
from karabo.native import Hash
from karabogui.conftest import gui_app
from karabogui.testing import click_button


def test_motor_stage_dialog(gui_app: gui_app):
    """Test the motor stage dialog of the motor assignment table"""
    old = Hash("gear", 2000)
    new = Hash("gear", 3000, "velocity", 10)
    terminal = "XHQ_BASE_OPTIC/MOTOR/1"
    stage = "QR123CODE"
    dialog = MotorConfigurationPreview(old, new, terminal, stage)
    assert dialog.windowTitle() == "Motor Configuration Comparison"

    def check_window_flag(bit, window_flags):
        return (bit & window_flags) == bit

    window_flags = dialog.windowFlags()
    for bit in [Qt.WindowStaysOnTopHint, Qt.WindowCloseButtonHint]:
        assert check_window_flag(bit, window_flags)

    title_info = dialog.info_label.text()
    assert terminal in title_info
    assert stage in title_info

    # Initial setting
    assert dialog.swap_button.text() == "Show Changes"
    click_button(dialog.swap_button)
    assert dialog.swap_button.text() == "Show Configuration"

    old = dialog.existing_changes_view.toPlainText()
    assert old == "\ngear\n2000\nvelocity\nMissing from configuration\n"
    new = dialog.new_changes_view.toPlainText()
    assert new == "\ngear\n3000\nvelocity\n10\n"
    config = dialog.configuration_view.toPlainText()
    assert config == "\ngear\n3000\nvelocity\n10\n"
