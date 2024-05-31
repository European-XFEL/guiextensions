from qtpy.QtCore import Qt
from qtpy.QtWidgets import QPushButton, QStackedWidget, QToolButton
from traits.api import Instance, WeakRef, on_trait_change

from karabogui import icons
from karabogui.api import is_proxy_allowed
from karabogui.binding.api import (
    BoolBinding, PropertyProxy, SlotBinding, get_binding_value)
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller)

from .models.api import DisplayConditionCommandModel

BUTTON_STYLE = """
QPushButton::enabled{
        color:black;
        border-color:green;
        background-color: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgb(255,255,255) ,
        stop: 1 rgb(237,237,237));

        border-width:3px;
        border-radius:5px;
        border-style:solid;
        padding: 3px;
        }

QPushButton::disabled{
        color : rgb(186, 186,186);
        border-color: rgb(149, 249, 133);
        background-color: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgb(255,255,255) ,
        stop: 1 rgb(237,237,237));

        border-width:3px;
        border-radius:5px;
        border-style:solid;
        padding: 3px;
        }

QPushButton::enabled::pressed{
        background-color: rgb(219, 219, 219);
        }
QPushButton::hover{
        background-color: rgb(255, 255, 255);
        }
"""
WARNING_STYLE = """
QToolButton{
    border-color:black;
    border-style:solid;
    border-width:3px;
    border-radius:5px;
    background-color: qlineargradient(
    x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgb(255,255,255) ,
    stop: 1 rgb(237,237,237));
    padding: 2px;
    }
"""


def is_compatible(binding):
    """Only for SlotBindings"""
    return isinstance(binding, SlotBinding)


@register_binding_controller(ui_name="Conditional Command",
                             klassname="ConditionCommand",
                             binding_type=(BoolBinding, SlotBinding),
                             is_compatible=is_compatible,
                             priority=-10,
                             can_show_nothing=False)
class DisplayConditionCommand(BaseBindingController):
    # The scene model class for this controller
    model = Instance(DisplayConditionCommandModel, args=())
    # Internal traits
    _button = WeakRef(QPushButton)

    _condition_proxy = Instance(PropertyProxy)

    def create_widget(self, parent):
        # The ToolButton is affected with bounded actions, thus we need to
        # create another (parent) widget where we can bind the actions.
        widget = QStackedWidget(parent)

        self._button = QPushButton(widget)
        self._button.setText("NO TEXT")
        self._button.clicked.connect(self.execute_action)

        warning_label = QToolButton(widget)
        warning_label.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        warning_label.setIcon(icons.propertyMissing)
        warning_label.setText("Add a bool property")
        warning_label.setStyleSheet(WARNING_STYLE)

        widget.addWidget(warning_label)
        widget.addWidget(self._button)

        return widget

    def add_proxy(self, proxy):
        """Add an additional proxy besides the main proxy to the controller
        """
        if self._condition_proxy is not None:
            # Don't allow a second boolean proxy!
            return False
        binding = proxy.binding
        if binding is None:
            # condition proxy device is offline
            self.widget.setCurrentIndex(1)
            self._set_button_enabled()
            self._button.setStyleSheet(BUTTON_STYLE)
            return True
        if isinstance(binding, BoolBinding):
            self.value_update(proxy)
            self._button.setStyleSheet(BUTTON_STYLE)
            self.widget.setCurrentIndex(1)
            return True
        return False

    def binding_update(self, proxy):
        """We received a binding_update and know about the attributes"""
        if proxy is self.proxy:
            displayed_name = proxy.binding.displayed_name or proxy.path
            self._button.setText(displayed_name)
        elif proxy is self._condition_proxy:
            self.value_update(proxy)

    def value_update(self, proxy):
        binding = proxy.binding
        if binding is None or not isinstance(binding, BoolBinding):
            return
        self._condition_proxy = proxy
        self._set_button_enabled()
        self.widget.setCurrentIndex(1)

    def state_update(self, proxy):
        binding = proxy.binding
        if isinstance(binding, SlotBinding):
            self._set_button_enabled()

    # ---------------------------------------------------------------------

    def setEnabled(self, enable):
        """Reimplemented to account for access level changes"""
        self.widget.setEnabled(enable)

    def execute_action(self):
        """Execute the action on the command proxy"""
        self.proxy.execute()

    @on_trait_change('proxy.root_proxy.status, '
                     '_condition_proxy.root_proxy.status')
    def _proxy_status_changed(self, _):
        """ Disable the button if the proxy device or condition_proxy device go
        offline."""
        if self._button is None or self._condition_proxy is None:
            return
        self._set_button_enabled()

    def _set_button_enabled(self):
        if self._condition_proxy is None:
            self._button.setEnabled(False)
            return
        binding = self._condition_proxy.binding
        if (binding is None or not isinstance(binding, BoolBinding) or
                self.proxy.root_proxy.state_binding is None):
            return
        value = get_binding_value(binding, None)
        condition_proxy_online = self._condition_proxy.root_proxy.online
        proxy_online = self.proxy.root_proxy.online
        allowed = condition_proxy_online and proxy_online
        allowed = allowed and bool(value) and is_proxy_allowed(self.proxy)
        self._button.setEnabled(allowed)
        self._button.setStyleSheet(BUTTON_STYLE)
