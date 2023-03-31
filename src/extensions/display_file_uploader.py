#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

import sys

from qtpy.QtWidgets import QToolButton, QVBoxLayout, QWidget
from traits.api import Instance, WeakRef

from karabo.common.api import WeakMethodRef
from karabogui.api import (
    BaseBindingController, WidgetNodeBinding, call_device_slot,
    get_binding_value, get_reason_parts, getOpenFileName, messagebox,
    register_binding_controller, with_display_type)

from .models.api import FileUploaderModel

_SIZE_LIMIT_FILE = 102400  # 100 KB


@register_binding_controller(
    ui_name="FileUploader Widget",
    klassname="FileUploader",
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type("WidgetNode|FileUploader"),
    priority=0, can_show_nothing=False)
class DisplayFileUploader(BaseBindingController):
    """The FileUploader enables to upload a file content as bytes to a
    Karabo device


    Schema: Node
              -> allowed (Bool) -> state
              -> info (String) -> tooltip
    """

    model = Instance(FileUploaderModel, args=())
    toolbutton = WeakRef(QToolButton)

    def create_widget(self, parent):
        widget = QWidget(parent)

        layout = QVBoxLayout(widget)

        self.toolbutton = QToolButton(widget)
        self.toolbutton.clicked.connect(self._request_content)
        layout.addWidget(self.toolbutton)

        return widget

    def binding_update(self, proxy):
        display_name = proxy.binding.displayed_name or proxy.path
        self.toolbutton.setText(display_name)

    def _request_content(self):
        fn = getOpenFileName(parent=self.widget)
        if not fn:
            return

        try:
            with open(fn, "rb") as fp:
                data = fp.read()
        except BaseException as e:
            messagebox.show_error(f"Could not read file {fn}.",
                                  details=f"{e}", parent=self.widget)
            return

        # Check if data size is larger than the limit
        file_size = sys.getsizeof(data)
        if file_size > _SIZE_LIMIT_FILE:
            messagebox.show_error(
                f"File size of {file_size} bytes is larger than "
                f"the allowed size of {_SIZE_LIMIT_FILE} bytes.",
                parent=self.widget)
            return

        handler = WeakMethodRef(self._upload_handler)
        call_device_slot(
            handler, self.getInstanceId(),
            "requestAction", action="upload", data=data, path=self.proxy.path)

    def _upload_handler(self, success, reply):
        if not success:
            reason, details = get_reason_parts(reply)
            messagebox.show_error(
                f"Upload request was not successful: {reason}",
                details=details, parent=self.widget)

    def value_update(self, proxy):
        node = get_binding_value(proxy.binding)
        if node is None:
            return

        allowed = get_binding_value(node.allowed)
        if allowed is None:
            return

        self.widget.setEnabled(allowed)
        info = get_binding_value(node.info)
        self.widget.setToolTip(info)
