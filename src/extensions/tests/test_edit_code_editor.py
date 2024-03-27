import pytest
from qtpy.QtWidgets import QMessageBox

from extensions.edit_code_editor import (
    CodeEditor, DisplayCodeEditor, compare_code)
from karabo.native import Configurable, String
from karabogui.binding.api import DeviceProxy, PropertyProxy, build_binding


class StringObject(Configurable):
    file_path = String(displayedName="File Path", displayType="CodeEditor")


@pytest.fixture()
def controller(gui_app, mocker):
    schema = StringObject.getClassSchema()
    binding = build_binding(schema)
    root_proxy = DeviceProxy(
        device_id="device_id", server_id="server_id", binding=binding)

    proxy = PropertyProxy(root_proxy=root_proxy)
    controller = DisplayCodeEditor(proxy=proxy)
    controller.__dict__["compare_and_save"] = mocker.Mock()
    controller.__dict__["fetch_code"] = mocker.Mock()
    controller.create(parent=None)
    assert controller is not None
    return controller


def test_editor_controller(controller, mocker):
    code = "hello\nworld"
    editor = controller.widget
    editor.set_code(code)
    assert editor.code_book.getEditorCode() == code

    mocker.patch("extensions.edit_code_editor.QMessageBox.question",
                 return_value=QMessageBox.Yes)
    # Save code
    editor.onSaveClicked()
    assert controller.compare_and_save.call_count == 1

    # Reload code
    editor.reloadRequested.emit()
    assert controller.fetch_code.call_count == 1


def test_compare_code():
    code1 = "Hello\nWorld"
    code2 = "Hello\nWorld"
    code3 = "Hello \nWorld"
    assert compare_code(code1, code2)
    assert not compare_code(code1, code3)


def test_editor_widget():
    """Test the widget changes when file_path changed"""
    editor_widget = CodeEditor()
    # Initial state
    editor_widget._file_path = "/path/to/the/code/file"
    editor_widget.set_code("Hello EXFEL")
    assert editor_widget.code_book.getEditorCode() == "Hello EXFEL"
    assert editor_widget.code_book.isEnabled()
    assert editor_widget.label.text() == "/path/to/the/code/file"
    assert "color:red" not in editor_widget.label.styleSheet()

    # File path changed
    editor_widget.file_path_changed("/a/new/code/file")
    assert not editor_widget.code_book.isEnabled()
    assert "color:red" in editor_widget.label.styleSheet()
    text = ("The file path has been changed. Press Reload to enable the "
            "editor with the new content.")
    assert editor_widget.label.text() == text
