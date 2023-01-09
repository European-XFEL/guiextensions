
try:
    from karabogui.binding.api import ProxyStatus
except ImportError:
    # compatibility with GUI version < 2.16
    from karabo.common.api import ProxyStatus

from karabo.native import (
    Bool, Configurable, Hash, String, Timestamp, VectorHash)
from karabogui.binding.api import (
    DeviceClassProxy, PropertyProxy, build_binding)
from karabogui.testing import GuiTestCase, set_proxy_value

from ..edit_scantool_templates import ScantoolTemplates


class ScanTemplateRow(Configurable):
    name = String()

    timestamp = String()

    loadTemplate = Bool()

    removeTemplate = Bool()


class ScanTemplates(Configurable):

    templates = VectorHash(
        rows=ScanTemplateRow)


class TestScantoolTemplatesWidget(GuiTestCase):

    def setUp(self):
        super(TestScantoolTemplatesWidget, self).setUp()

        schema = ScanTemplates.getClassSchema()
        self.binding = build_binding(schema)
        device = DeviceClassProxy(binding=self.binding,
                                  server_id='KarabaconServer',
                                  status=ProxyStatus.ONLINE)
        self.templates_proxy = PropertyProxy(
            root_proxy=device, path='templates')

        # Create the controllers and initialize their widgets
        self.controller = ScantoolTemplates(proxy=self.templates_proxy)
        self.controller.create(None)

    def tearDown(self):
        super(TestScantoolTemplatesWidget, self).tearDown()
        self.controller.destroy()

    def test_device_groups(self):
        self.assertIsNotNone(self.controller.widget)

        data = [Hash("name", "template1", "timestamp", Timestamp().toLocal(),
                     "loadTemplate", True, "removeTemplate", True),
                Hash("name", "template2", "timestamp", Timestamp().toLocal(),
                     "loadTemplate", True, "removeTemplate", True),
                Hash("name", "template3", "timestamp", Timestamp().toLocal(),
                     "loadTemplate", True, "removeTemplate", True)]
        set_proxy_value(self.templates_proxy, "templates", data)
        cbox = self.controller.templates_cbox
        for index in range(cbox.count()):
            self.assertEqual(cbox.itemText(index),
                             data[index]["name"])
        self.assertEquals(cbox.currentText(), "template3")
