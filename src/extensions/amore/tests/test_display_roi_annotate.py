from extensions.amore.display_roi_annotate import DisplayImageAnnotate
from karabogui.testing import GuiTestCase


class TestDisplayImageAnnotate(GuiTestCase):
    def test_annotate_display(self):
        """Test that at least the imports are working"""
        image_annotate = DisplayImageAnnotate()
        self.assertIsNotNone(image_annotate)
