from karabogui.testing import GuiTestCase

from ...const import ADD, MOTOR_NAMES, REMOVE, SOURCE_NAMES, X_DATA, Y_DATA
from ..xy_data import XYDataSelectionWidget


class TestXYDataSelectionController(GuiTestCase):

    def setUp(self):
        super(TestXYDataSelectionController, self).setUp()
        self._widget = XYDataSelectionWidget()
        self._widget.changed.connect(self._mock_slot)
        self._widget.show()
        self._changes = None

    def tearDown(self):
        self._widget.close()
        self._widget.changed.disconnect()
        self._widget.destroy()
        self._widget = None

    def _mock_slot(self, changes):
        self._changes = changes

    def test_basics(self):
        self._assert_motors(names=MOTOR_NAMES, index=0)
        self._assert_sources(names=SOURCE_NAMES, checked=[])
        self._assert_changes(changes=None)

    def test_set_devices(self):
        # Set and assert motors
        motors = MOTOR_NAMES[:2]
        self._widget.set_motors(motors)
        self._assert_motors(names=motors, index=0)
        self._assert_changes(changes=None)

        # Set and assert devices
        sources = SOURCE_NAMES[:3]
        self._widget.set_sources(sources)
        self._assert_sources(names=sources, checked=[])
        self._assert_changes(changes=None)

    def test_set_config(self):
        # Set devices
        motors = MOTOR_NAMES[:2]
        self._widget.set_motors(motors)
        sources = SOURCE_NAMES[:3]
        self._widget.set_sources(sources)

        # Set config
        x_data = motors[1]
        y_data_list = sources[1:]
        config = [{X_DATA: x_data, Y_DATA: y_data} for y_data in y_data_list]
        self._widget.set_config(config)

        # Assert widgets
        self._assert_motors(names=motors, index=1)
        self._assert_sources(names=sources, checked=y_data_list)
        self._assert_changes(changes=None)

    def test_changes(self):
        # Set devices
        motors = MOTOR_NAMES[:2]
        self._widget.set_motors(motors)
        sources = SOURCE_NAMES[:3]
        self._widget.set_sources(sources)

        # Set config
        x_data = motors[1]
        y_data_list = sources[1:]
        config = [{X_DATA: x_data, Y_DATA: y_data} for y_data in y_data_list]
        self._widget.set_config(config)

        # Change x_data by setting the combobox current index
        # to the first motor
        x_index = 0
        combobox = self._widget.ui_x_combobox
        combobox.setCurrentIndex(x_index)
        self._assert_changes(changes={X_DATA: motors[x_index]})

        # Remove y_data by unchecking one source
        y_index = 1
        checkbox = self._widget._checkboxes[y_index]
        self.assertTrue(checkbox.isChecked())
        checkbox.click()
        self._assert_changes(removed={Y_DATA: sources[y_index]})

        # Add y_data by checking one source
        y_index = 1
        checkbox = self._widget._checkboxes[y_index]
        self.assertFalse(checkbox.isChecked())
        checkbox.click()
        self._assert_changes(added={Y_DATA: sources[y_index]})

    def test_last_item(self):
        # Set devices
        motors = MOTOR_NAMES[:2]
        self._widget.set_motors(motors)
        sources = SOURCE_NAMES[:3]
        self._widget.set_sources(sources)

        # Set config, only put one source
        y_index = 1
        config = [{X_DATA: motors[1], Y_DATA: sources[y_index]}]
        self._widget.set_config(config)

        y_index = 1
        checkbox = self._widget._checkboxes[y_index]
        self.assertTrue(checkbox.isChecked())
        checkbox.click()
        self._assert_changes(changes=None)

    def _assert_motors(self, *, names, index):
        combobox = self._widget.ui_x_combobox
        items = [combobox.itemText(i) for i in range(combobox.count())]
        self.assertListEqual(items, names)
        self.assertEqual(combobox.currentIndex(), index)

    def _assert_sources(self, *, names, checked):
        checkboxes = [checkbox for checkbox in self._widget._checkboxes
                      if checkbox.isVisible()]
        self.assertListEqual([checkbox.text() for checkbox in checkboxes],
                             names)
        checked_boxes = [checkbox.text() for checkbox in checkboxes
                         if checkbox.isChecked()]
        self.assertListEqual(checked_boxes, checked)

    def _assert_changes(self, changes=None, removed=None, added=None):
        if (changes, removed, added) == (None, None, None):
            self.assertIsNone(self._changes)
            return

        x_remove, y_remove = set(), set()
        x_add, y_add = set(), set()

        if REMOVE in self._changes:
            for conf in self._changes[REMOVE]:
                x_remove.add(conf[X_DATA])
                y_remove.add(conf[Y_DATA])

        if ADD in self._changes:
            for conf in self._changes[ADD]:
                x_add.add(conf[X_DATA])
                y_add.add(conf[Y_DATA])

        if changes is not None and X_DATA in changes:
            self.assertNotEqual(x_remove, x_add)
            self.assertEqual(changes[X_DATA], next(iter(x_add)))
            self.assertSetEqual(y_remove, y_add)
        elif removed is not None and Y_DATA in removed:
            self.assertTrue(removed[Y_DATA] in y_remove)
        elif added is not None and Y_DATA in added:
            self.assertTrue(added[Y_DATA] in y_add)

        # Reset!
        self._changes = None
