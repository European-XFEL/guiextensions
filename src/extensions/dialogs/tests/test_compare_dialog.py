from unittest import main

from extensions.dialogs.api import CompareDialog
from karabo.native import Hash
from karabogui.testing import GuiTestCase


class TestCompareDialog(GuiTestCase):

    def test_basics(self):
        # Single device
        data = Hash("deviceA", Hash("old", Hash("a", 1, "b", True),
                                    "new", Hash("a", 2, "b", True)))
        dialog = CompareDialog("Compare deviceA", data)
        self.assertEqual(dialog.ui_title.text(), "Compare deviceA")
        self.assertEqual(dialog.ui_stack_widget.count(), 1)

        # Two device
        data = Hash("deviceA", Hash("old", Hash("a", 1, "b", True),
                                    "new", Hash("a", 2, "b", True)),
                    "deviceB", Hash("old", Hash("a", 4, "b", True),
                                    "new", Hash("a", 3, "b", False)))
        dialog = CompareDialog("Compare deviceA and B", data)
        self.assertEqual(dialog.ui_title.text(), "Compare deviceA and B")
        self.assertEqual(dialog.ui_stack_widget.count(), 2)


if __name__ == "__main__":
    main()
