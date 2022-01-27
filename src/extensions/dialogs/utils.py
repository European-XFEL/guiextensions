from pathlib import Path


def get_dialog_ui(ui_name):
    """Retrieve the appropriate `.ui` file from the ui folder
    """
    assert ui_name.endswith(".ui"), f"{ui_name} is not a `.ui` file"

    return str(Path(__file__).parent / "ui" / ui_name)
