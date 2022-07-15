from karabo.common.states import State
from karabo.native import AccessLevel, Bool, Configurable, Slot, String
from karabogui.binding.api import (
    DeviceProxy, PropertyProxy, ProxyStatus, apply_default_configuration,
    build_binding)
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_value)

from ..display_condition import DisplayConditionCommand


class SlotObject(Configurable):
    state = String(defaultValue=State.ACTIVE)

    @Slot(allowedStates=[State.ACTIVE],
          requiredAccessLevel=AccessLevel.OBSERVER)
    def yep(self):
        pass


class BoolObject(Configurable):
    prop = Bool()


class TestDisplayCondition(GuiTestCase):

    def setUp(self):
        super().setUp()
        schema = SlotObject.getClassSchema()
        binding = build_binding(schema)
        apply_default_configuration(binding)
        dev_proxy = DeviceProxy(device_id="dev", server_id="swerver",
                                binding=binding)
        proxy = PropertyProxy(root_proxy=dev_proxy, path="yep")
        controller = DisplayConditionCommand(proxy=proxy)
        controller.create(parent=None)
        self.controller = controller
        self.proxy = proxy

        bool_schema = BoolObject.getClassSchema()
        bool_proxy = get_class_property_proxy(bool_schema, "prop")
        self.bool_proxy = bool_proxy

    def test_stacked_widget(self):
        """ Test the widget display in stacked widget with and without proxy
        """
        assert self.controller.widget.currentIndex() == 0
        self.controller.add_proxy(self.bool_proxy)
        assert self.controller.widget.currentIndex() == 1

    def test_controller_widget_enabled(self):
        """ Test the controller widget (QPushButton) gets enabled when proxy
        binding value is True
        """
        bool_proxy = self.bool_proxy
        bool_proxy.value = True
        assert self.controller.add_proxy(bool_proxy)
        assert self.controller._button.isEnabled()

    def test_controller_widget_disabled(self):
        """
        Test the controller widget (QPushButton) gets disabled when proxy
        binding value is False
        """
        bool_proxy = self.bool_proxy
        bool_proxy.value = False
        assert self.controller.add_proxy(bool_proxy)
        assert not self.controller._button.isEnabled()

    def test_second_proxy(self):
        """ Adding a second proxy should fail.
        """
        assert self.controller.add_proxy(self.bool_proxy)
        assert not self.controller.add_proxy(self.bool_proxy)

    def test_enabled(self):
        """
        Test the enabled status of the button when the proxy device and
        condition_proxy devices go offline/online.
        """
        online = ProxyStatus.ONLINE
        offline = ProxyStatus.OFFLINE
        self.controller.add_proxy(self.bool_proxy)
        self.controller.proxy.root_proxy.status = offline
        assert not self.controller._button.isEnabled()

        self.controller.proxy.root_proxy.status = online
        self.controller._condition_proxy.root_proxy.status = online
        assert self.controller._button.isEnabled()

        self.controller._condition_proxy.root_proxy.status = offline
        assert not self.controller._button.isEnabled()

    def test_state_update(self):
        """Test the Slot proxy state change enables/disables the button."""
        self.bool_proxy.value = True
        self.controller.add_proxy(self.bool_proxy)
        assert self.controller._button.isEnabled()

        set_proxy_value(self.proxy, 'state', State.INIT.value)
        assert not self.controller._button.isEnabled()

        set_proxy_value(self.proxy, 'state', State.ACTIVE.value)
        assert self.controller._button.isEnabled()
