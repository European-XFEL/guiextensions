import pytest

from extensions.edit_code_editor import DisplayCodeEditor, compare_code
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
    controller.__dict__["saveCode"] = mocker.Mock()
    controller.__dict__["fetch_code"] = mocker.Mock()
    controller.create(parent=None)
    assert controller is not None
    return controller


def test_editor_widget(controller, mocker):
    code = "hello\nworld"
    editor = controller.widget
    editor.set_code(code)
    assert editor.code_book.getEditorCode() == code

    mocker.patch("extensions.edit_code_editor.QMessageBox.question",
                 return_value=True)
    # Save code
    editor.onSaveClicked()
    assert controller.saveCode.call_count == 1
    controller.saveCode.assert_called_with(code)

    # Reload code
    editor.reloadRequested.emit()
    assert controller.fetch_code.call_count == 1


def test_compare_code():
    code1 = "Hello\nWorld"
    code2 = "Hello\nWorld"
    code3 = "Hello \nWorld"
    assert compare_code(code1, code2)
    assert not compare_code(code1, code3)
