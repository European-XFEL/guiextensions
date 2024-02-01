import hashlib

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QToolButton, QVBoxLayout)
from traits.api import Instance

from extensions.utils import gui_version_compatible
from karabo.native import Hash
from karabogui.api import (
    BaseBindingController, StringBinding, call_device_slot, generateObjectName,
    get_logger, get_reason_parts, icons, messagebox,
    register_binding_controller, with_display_type)

from .models.api import MetroEditorModel

if gui_version_compatible(2, 20):
    from karabogui.api import CodeBook, ToolBar
else:
    from karabogui.widgets.scintilla_editor import CodeBook
    from karabogui.widgets.toolbar import ToolBar


@register_binding_controller(ui_name="Code Editor Widget", can_edit=False,
                             klassname="CodeEditor",
                             binding_type=StringBinding,
                             is_compatible=with_display_type("CodeEditor"),
                             priority=0)
class DisplayCodeEditor(BaseBindingController):
    """A controller with a Code Editor for Python.
    The Device which uses the controllers must have the slot methods
    `slotGetCode` and `slotWriteCode` defined. """

    model = Instance(MetroEditorModel, args=())

    def create_widget(self, parent):
        widget = CodeEditor(parent=parent)
        widget.saveRequested.connect(self.saveCode)
        widget.reloadRequested.connect(self.fetch_code)
        return widget

    def value_update(self, proxy):
        self.widget.update_label(str(proxy.value))

    def clear_widget(self):
        self.widget.clear()

    def fetch_code(self):

        def handler(success, reply):
            if success:
                code = reply.get("code")
                self.widget.set_code(code)
            else:
                reason, details = get_reason_parts(reply)
                messagebox.show_error(
                    f"Failed to read the code from the file{reason}",
                    details=details, parent=self.widget)

        instance_id = self.getInstanceId()
        slot_name = "slotGetCode"
        call_device_slot(handler, instance_id, slot_name)

    def saveCode(self, code):
        logger = get_logger()

        def handler(success, reply):
            if success:
                logger.info("Successfully saved the code to the file")
            else:
                reason, details = get_reason_parts(reply)
                messagebox.show_error(
                    f"Failed to save to the file {reason}", details=details,
                    parent=self.widget)

        instance_id = self.getInstanceId()
        slot_name = "slotWriteCode"
        params = Hash("code", code)
        call_device_slot(handler, instance_id, slot_name, params=params)


class CodeEditor(QFrame):

    saveRequested = Signal(str)
    reloadRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        object_name = generateObjectName(self)
        self.setObjectName(object_name)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        self.code_book = CodeBook(parent=self)
        self.code_book.setMinimumSize(680, 400)
        self.code_book.qualityChecked.connect(self.updateCodeQualityIcon)
        self.code_book.codeChanged.connect(self.onCodeChanged)
        layout.addWidget(self.code_book)
        self.setStyleSheet(
             f"QFrame[objectName = '{object_name}'] {{ "
             f"border: 1px solid gray;}}")
        self.label = QLabel(parent=self)
        self.label.setContentsMargins(5, 0, 0, 0)
        layout.addWidget(self.label)

    def _create_toolbar(self):
        toolbar_widget = QFrame(self)
        object_name = generateObjectName(toolbar_widget)
        toolbar_widget.setObjectName(object_name)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_widget.setStyleSheet(
            f" QFrame[objectName = '{object_name}'] {{ "
            f"background-color: gray;}}")

        toolbar = ToolBar(parent=toolbar_widget)

        toolbar.addAction(icons.zoomIn, "Increase font", self.increaseFont)
        toolbar.addAction(icons.zoomOut, "Decrease font", self.decreaseFont)

        toolbar.addSeparator()
        self.check_button = toolbar.addAction(
            icons.inspect_code, "Check Code Quality", self.checkCode)
        self.clear_button = toolbar.addAction(
            icons.editClear, "Clear Linter Messages", self.clearIndicators)
        self.clear_button.setVisible(False)

        toolbar_layout.addStretch()
        reload_button = QToolButton(parent=toolbar_widget)
        reload_button.setIcon(icons.refresh)
        reload_button.setToolTip("Reload Code")
        reload_button.clicked.connect(self.reloadRequested)
        toolbar_layout.addWidget(reload_button)

        save_button = QToolButton(parent=toolbar_widget)
        save_button.setText("Save")
        save_button.setToolTip("Save Code")
        save_button.clicked.connect(self.onSaveClicked)
        toolbar_layout.addWidget(save_button)

        return toolbar_widget

    @Slot()
    def onSaveClicked(self):
        question = "Do you want to save the changes?"
        reply = QMessageBox.question(self, "Save to File", question,
                                     QMessageBox.Yes | QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return
        code = self.code_book.getEditorCode()
        self.saveRequested.emit(code)

    def _setClearButtonVisibility(self):
        """ The 'clear_button' should be visible only when the issues are
        annotated."""
        has_annotation = self.code_book.code_editor.has_annotation
        self.clear_button.setVisible(has_annotation)

    @Slot(bool)
    def updateCodeQualityIcon(self, error):
        """ Set the icon on 'check_button' depending on whether the code
        has any error or not. """
        icon = icons.inspect_code_error if error else icons.inspect_code_ok
        self.check_button.setIcon(icon)
        self._setClearButtonVisibility()

    @Slot()
    def onCodeChanged(self):
        self.check_button.setIcon(icons.inspect_code)
        self._setClearButtonVisibility()

    @Slot()
    def increaseFont(self):
        self.code_book.increaseFontSize()

    @Slot()
    def decreaseFont(self):
        self.code_book.decreaseFontSize()

    @Slot()
    def checkCode(self):
        self.code_book.checkCode()

    @Slot()
    def clearIndicators(self):
        self.code_book.clearIndicators()
        self.clear_button.setVisible(True)

    def set_code(self, code: str):
        current_code = self.code_book.getEditorCode()
        if current_code.strip():
            # Check if the code in editor is different before reloading from
            # the file.
            code_same = compare_code(code, current_code)
            if not code_same:
                question = "Code is different. Do you wish to overwrite?"
                reply = QMessageBox.question(
                    self, "Overwrite", question,
                    QMessageBox.Yes | QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return
        self.code_book.code_editor.setText(code)
        self.label.setStyleSheet("")

    def clear(self):
        self.code_book.clear()

    def update_label(self, file_path: str):
        self.label.setText(file_path)
        self.label.setStyleSheet("color:red")


def compare_code(first_code: str, second_code: str):
    """A quick comparison of the codes."""
    hash1 = hashlib.sha256(first_code.encode()).hexdigest()
    hash2 = hashlib.sha256(second_code.encode()).hexdigest()
    return hash1 == hash2
