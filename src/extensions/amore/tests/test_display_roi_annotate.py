from extensions.amore.display_roi_annotate import DisplayImageAnnotate


def test_annotate_display(gui_app):
    """Test that at least the imports are working"""
    image_annotate = DisplayImageAnnotate()
    assert image_annotate is not None
