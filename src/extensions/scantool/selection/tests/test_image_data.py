from karabogui.testing import GuiTestCase

from ...const import (
    ADD, MOTOR_NAMES, REMOVE, SOURCE_NAMES, TEST_MOTOR_IDS, TEST_SOURCE_IDS,
    X_DATA, Y_DATA, Z_DATA)
from ..image_data import ImageDataSelectionWidget


class TestImageDataSelectionController(GuiTestCase):

    def setUp(self):
        super(TestImageDataSelectionController, self).setUp()
        self._widget = ImageDataSelectionWidget()
        self._widget.changed.connect(self._mock_slot)
        self._widget.show()
        self._changes = None

    def tearDown(self):
        super(TestImageDataSelectionController, self).tearDown()
        self._widget.close()
        self._widget.changed.disconnect()
        self._widget.destroy()
        self._widget = None

    def _mock_slot(self, changes):
        self._changes = changes

    def test_basics(self):
        self._widget.set_motors(MOTOR_NAMES, TEST_MOTOR_IDS)
        self._widget.set_sources(SOURCE_NAMES, TEST_SOURCE_IDS)

        self._assert_motors(names=TEST_MOTOR_IDS)
        self._assert_sources(names=TEST_SOURCE_IDS, checked=[])
        self._assert_changes(changes=None)

    def test_set_devices(self):
        # Set and assert motors
        motors = MOTOR_NAMES[:2]
        motor_ids = TEST_MOTOR_IDS[:2]
        self._widget.set_motors(motors, motor_ids)
        self._assert_motors(names=motor_ids)
        self._assert_changes(changes=None)

        # Set and assert devices
        sources = SOURCE_NAMES[:3]
        source_ids = TEST_SOURCE_IDS[:3]
        self._widget.set_sources(sources, source_ids)
        self._assert_sources(names=source_ids, checked=[])
        self._assert_changes(changes=None)

    def test_set_config(self):
        # Set devices
        motors = MOTOR_NAMES[:2]
        motor_ids = TEST_MOTOR_IDS[:2]
        self._widget.set_motors(motors, motor_ids)
        sources = SOURCE_NAMES[:3]
        source_ids = TEST_SOURCE_IDS[:3]
        self._widget.set_sources(sources, source_ids)

        # Set config
        x_index = 1
        y_index = 0
        z_index = 2
        config = [{X_DATA: motor_ids[x_index],
                   Y_DATA: motor_ids[y_index],
                   Z_DATA: source_ids[z_index]}]
        self._widget.set_config(config)

        # Assert widgets
        self._assert_motors(names=motor_ids, x_index=x_index, y_index=y_index)
        self._assert_sources(names=source_ids, checked=[source_ids[z_index]])
        self._assert_changes(changes=None)

    def test_changes(self):
        # Set devices
        motors = MOTOR_NAMES[:2]
        motor_ids = TEST_MOTOR_IDS[:2]
        self._widget.set_motors(motors, motor_ids)
        sources = SOURCE_NAMES[:3]
        source_ids = TEST_SOURCE_IDS[:3]
        self._widget.set_sources(sources, source_ids)

        # Set config
        x_index = 1
        y_index = 0
        z_index = 2
        config = [{X_DATA: motor_ids[x_index],
                   Y_DATA: motor_ids[y_index],
                   Z_DATA: source_ids[z_index]}]
        self._widget.set_config(config)

        # Add z_data by checking one source
        checkbox = self._widget._source_widgets[z_index]
        self.assertTrue(checkbox.isChecked())
        checkbox.click()
        self._assert_changes(changes=None)

    def test_last_item(self):
        # Set devices
        motors = MOTOR_NAMES[:2]
        motor_ids = TEST_MOTOR_IDS[:2]
        self._widget.set_motors(motors, motor_ids)
        sources = SOURCE_NAMES[:3]
        source_ids = TEST_SOURCE_IDS[:3]
        self._widget.set_sources(sources, source_ids)

        # Set config
        x_index = 1
        y_index = 0
        z_index = 2
        config = [{X_DATA: motor_ids[x_index],
                   Y_DATA: motor_ids[y_index],
                   Z_DATA: source_ids[z_index]}]
        self._widget.set_config(config)

        checkbox = self._widget._source_widgets[z_index]
        self.assertTrue(checkbox.isChecked())
        checkbox.click()
        self._assert_changes(changes=None)

    def _assert_motors(self, *, x_index=0, y_index=1, names):
        x_combobox = self._widget.ui_x_combobox
        items = [x_combobox.itemText(i) for i in range(x_combobox.count())]
        self.assertListEqual(items, names)
        self.assertEqual(x_combobox.currentIndex(), x_index)

        y_combobox = self._widget.ui_y_combobox
        items = [y_combobox.itemText(i) for i in range(y_combobox.count())]
        self.assertListEqual(items, names)
        self.assertEqual(y_combobox.currentIndex(), y_index)

    def _assert_sources(self, *, names, checked):
        checkboxes = [checkbox for checkbox in self._widget._source_widgets
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

        x_remove, y_remove, z_remove = set(), set(), set()
        x_add, y_add, z_add = set(), set(), set()

        if REMOVE in self._changes:
            for conf in self._changes[REMOVE]:
                x_remove.add(conf[X_DATA])
                y_remove.add(conf[Y_DATA])
                z_remove.add(conf[Z_DATA])

        if ADD in self._changes:
            for conf in self._changes[ADD]:
                x_add.add(conf[X_DATA])
                y_add.add(conf[Y_DATA])
                z_add.add(conf[Z_DATA])

        self.assertEqual(x_remove, x_add)
        self.assertEqual(y_remove, y_add)
        self.assertTrue(removed[Z_DATA] in z_remove)
        self.assertTrue(added[Z_DATA] in z_add)

        # Reset!
        self._changes = None
