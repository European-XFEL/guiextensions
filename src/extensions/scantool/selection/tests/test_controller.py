from karabogui.testing import GuiTestCase

from ..controller import (
    DataSelectionController, ImageDataSelectionWidget, XYDataSelectionWidget)


class TestSelectionController(GuiTestCase):

    def setUp(self):
        super(TestSelectionController, self).setUp()
        self._controller = DataSelectionController()

    def test_basics(self):
        self.assertIsNone(self._controller._selection_widget)
        self.assertEqual(self._controller.widget.layout().count(), 0)

    def test_use_selection(self):
        self._controller.use_xy_selection()
        self._assert_widget(XYDataSelectionWidget)

        self._controller.use_image_selection()
        self._assert_widget(ImageDataSelectionWidget)

    def _assert_widget(self, klass):
        widget = self._controller._selection_widget
        self.assertIsNotNone(widget)
        self.assertTrue(isinstance(widget, klass))
