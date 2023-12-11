import os.path as op


def get_panel_ui(ui_name):
    assert ui_name.endswith(".ui"), f"{ui_name} is not a `.ui` file"

    return op.join(op.abspath(op.dirname(__file__)), "ui", ui_name)
