
try:
    from karabogui.binding.api import ProxyStatus
except ImportError:
    # compatibility with GUI version < 2.16
    from karabo.common.api import ProxyStatus

from karabo.native import Bool, Configurable, Hash, String, VectorHash
from karabogui.binding.api import (
    DeviceClassProxy, PropertyProxy, build_binding)
from karabogui.testing import GuiTestCase, get_property_proxy, set_proxy_value

from ..display_scantool_device_view import DEVICE_PROXY_MAP, ScantoolDeviceView


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


class MotorEnvSchema(Configurable):

    motorEnv = VectorHash(
        rows=MotorRow,
        defaultValue=[])


class DataEnvSchema(Configurable):

    dataEnv = VectorHash(
        rows=DataSourceRow,
        defaultValue=[])


class TriggerEnvSchema(Configurable):

    triggerEnv = VectorHash(
        rows=TriggerRow,
        defaultValue=[])


class TestScantoolDeviceViewWidget(GuiTestCase):

    def setUp(self):
        super(TestScantoolDeviceViewWidget, self).setUp()

        schema = MotorEnvSchema.getClassSchema()
        self.binding = build_binding(schema)
        device = DeviceClassProxy(binding=self.binding,
                                  server_id='KarabaconServer',
                                  status=ProxyStatus.ONLINE)
        self.motor_env_proxy = PropertyProxy(root_proxy=device,
                                             path='motorEnv')

        schema = DataEnvSchema.getClassSchema()
        self.data_env_proxy = get_property_proxy(schema, 'dataEnv')

        schema = TriggerEnvSchema.getClassSchema()
        self.trigger_env_proxy = get_property_proxy(schema, 'triggerEnv')

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
        self.assertEqual(self.controller._treewidget.topLevelItemCount(),
                         len(DEVICE_PROXY_MAP))

    def test_env(self):
        data = [Hash("alias", "m1", "deviceId", "TEST_DEVICE", "axis",
                     "default", "active", "True")]
        set_proxy_value(self.motor_env_proxy, "motorEnv", data)

        self.assertTrue(self._has_group_item_child("Motors", "m1"))

        data = [Hash("alias", "s1", "deviceId", "TEST_SOURCE_1",
                     "source", "value", "active", "True")]
        set_proxy_value(self.data_env_proxy, "dataEnv", data)
        self.assertTrue(self._has_group_item_child("Sources", "s1"))

        data = [Hash("alias", "t1", "deviceId", "TEST_TRIGGER_1", "active",
                     "True")]
        set_proxy_value(self.trigger_env_proxy, "triggerEnv", data)
        self.assertTrue(self._has_group_item_child("Sources", "s1"))

    def _has_group_item_child(self, parent_text, child_text):
        treewidget = self.controller._treewidget
        for parent_index in range(treewidget.topLevelItemCount()):
            parent = treewidget.topLevelItem(parent_index)
            if parent.text(0) == parent_text:
                for child_index in range(parent.childCount()):
                    if parent.child(child_index).text(0) == child_text:
                        return True
