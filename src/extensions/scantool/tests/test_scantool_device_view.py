
from karabo.native import Bool, Configurable, Hash, Node, String, VectorHash
from karabogui.binding.api import (
    DeviceClassProxy, PropertyProxy, ProxyStatus, build_binding)
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_value

from ..display_scantool_device_view import (
    DEVICE_ATTRIBUTES_MAP, ScantoolDeviceView)


class MotorRow(Configurable):
    alias = String(
        displayedName="Alias",
        defaultValue="None")

    deviceId = String(
        displayedName="DeviceId",
        defaultValue='')

    axis = String(
        displayedName="Axis",
        defaultValue="default")

    active = Bool(
        displayedName="Active",
        defaultValue=False)


class DataSourceRow(Configurable):
    alias = String(
        displayedName="Alias",
        defaultValue="None")

    deviceId = String(
        displayedName="DeviceId",
        defaultValue='')

    source = String(
        displayedName="Key",
        defaultValue="")

    active = Bool(
        displayedName="Active",
        defaultValue=False)


class TriggerRow(Configurable):
    alias = String(
        displayedName="Alias",
        defaultValue="None")

    deviceId = String(
        displayedName="DeviceId",
        defaultValue='')

    active = Bool(
        displayedName="Active",
        defaultValue=False)


class DeviceEnvSchema(Configurable):

    motors = VectorHash(
        rows=MotorRow,
        defaultValue=[])

    sources = VectorHash(
        rows=DataSourceRow,
        defaultValue=[])

    triggers = VectorHash(
        rows=TriggerRow,
        defaultValue=[])


class DeviceEnv(Configurable):

    deviceEnv = Node(DeviceEnvSchema)


class TestScantoolDeviceViewWidget(GuiTestCase):

    def setUp(self):
        super(TestScantoolDeviceViewWidget, self).setUp()

        schema = DeviceEnv.getClassSchema()
        self.binding = build_binding(schema)
        device = DeviceClassProxy(binding=self.binding,
                                  server_id='KarabaconServer',
                                  status=ProxyStatus.ONLINE)
        self.motor_env_proxy = PropertyProxy(root_proxy=device,
                                             path='deviceEnv.motors')

        self.data_env_proxy = get_property_proxy(schema, 'deviceEnv.sources')
        self.trigger_env_proxy = get_property_proxy(
            schema, 'deviceEnv.triggers')

        # Create the controllers and initialize their widgets
        self.controller = ScantoolDeviceView(proxy=self.motor_env_proxy)
        self.controller.create(None)
        self.controller.visualize_additional_property(self.data_env_proxy)
        self.controller.visualize_additional_property(self.trigger_env_proxy)

    def tearDown(self):
        super(TestScantoolDeviceViewWidget, self).tearDown()
        self.controller.destroy()

    def test_init(self):
        self.assertIsNotNone(self.controller.widget)
        # Check if tree has group items
        treewidget = self.controller.widget._device_tree
        self.assertEqual(treewidget.topLevelItemCount(),
                         len(DEVICE_ATTRIBUTES_MAP))

    def test_env(self):
        data = [Hash("alias", "m1", "deviceId", "TEST_DEVICE", "axis",
                     "default", "active", "True")]
        set_proxy_value(self.motor_env_proxy, "deviceEnv.motors", data)

        self.assertTrue(self._has_group_item_child("Motors", "m1"))

        data = [Hash("alias", "s1", "deviceId", "TEST_SOURCE_1",
                     "source", "value", "active", "True")]
        set_proxy_value(self.data_env_proxy, "deviceEnv.sources", data)
        self.assertTrue(self._has_group_item_child("Sources", "s1"))

        data = [Hash("alias", "t1", "deviceId", "TEST_TRIGGER_1", "active",
                     "True")]
        set_proxy_value(self.trigger_env_proxy, "deviceEnv.triggers", data)
        self.assertTrue(self._has_group_item_child("Sources", "s1"))

    def _has_group_item_child(self, parent_text, child_text):
        treewidget = self.controller.widget._device_tree
        for parent_index in range(treewidget.topLevelItemCount()):
            parent = treewidget.topLevelItem(parent_index)
            if parent.text(0) == parent_text:
                for child_index in range(parent.childCount()):
                    if parent.child(child_index).text(0) == child_text:
                        return True
