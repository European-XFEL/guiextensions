from unittest.mock import patch

from qtpy.QtCore import QLocale

from extensions.edit_datetime_label import EditableDateTime
from extensions.models.api import EditableDateTimeModel
from karabo.common.states import State
from karabo.native import Configurable, Hash, String
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash, set_proxy_value)


class Object(Configurable):
    state = String(defaultValue=State.INIT)
    prop = String(displayType="Datetime",
                  allowedStates=[State.INIT])


class TestDateTimeEdit(GuiTestCase):
    def setUp(self):
        super().setUp()
        QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, "prop")

        self.controller = EditableDateTime(proxy=self.proxy,
                                           model=EditableDateTimeModel())
        self.controller.create(None)

    def test_set_value(self):
        h = Hash("prop", "2009-04-25")
        set_proxy_hash(self.proxy, h)
        self.assertEqual(self.controller.widget.text(), "2009-4-25T00:00:00")

        h = Hash("prop", "2009-04-22")
        set_proxy_hash(self.proxy, h)
        self.assertEqual(self.controller.widget.text(), "2009-4-22T00:00:00")

    def test_change_time_format(self):
        controller = EditableDateTime(proxy=self.proxy,
                                      model=EditableDateTimeModel())
        controller.create(None)
        tp = "2009-04-22T00:00:00"
        h = Hash("prop", tp)
        set_proxy_hash(self.proxy, h)

        self.assertEqual(controller.widget.text(), "2009-4-22T00:00:00")
        action = controller.widget.actions()[0]
        assert action.text() == "Change datetime format..."
        dsym = "extensions.edit_datetime_label.QInputDialog"
        with patch(dsym) as QInputDialog:
            new_format = "ddd MMMM d yy"
            QInputDialog.getText.return_value = new_format, True
            action.trigger()
            self.assertEqual(controller.model.time_format, new_format)

    def test_state_update(self):
        set_proxy_value(self.proxy, "state", "CHANGING")
        self.assertFalse(self.controller.widget.isEnabled())
        set_proxy_value(self.proxy, "state", "INIT")
        self.assertTrue(self.controller.widget.isEnabled())
        set_proxy_value(self.proxy, "state", "CHANGING")
        self.assertFalse(self.controller.widget.isEnabled())
