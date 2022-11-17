from pathlib import Path

from karabo.native import Hash, has_changes


def get_dialog_ui(ui_name):
    """Retrieve the appropriate `.ui` file from the ui folder
    """
    assert ui_name.endswith(".ui"), f"{ui_name} is not a `.ui` file"

    return str(Path(__file__).parent / "ui" / ui_name)


def get_config_changes(old, new):
    """Extract the changes of Hash `new` with respect to Hash `old`"""
    changes_old, changes_new = Hash(), Hash()

    old_paths = old.paths(intermediate=False)
    new_paths = new.paths(intermediate=False)

    keys = sorted(set(old_paths).union(set(new_paths)))
    for key in keys:
        old_value = old.get(key, None)
        new_value = new.get(key, None)
        if old_value is None and new_value is not None:
            changes_old[key] = "Missing from configuration"
            changes_new[key] = new_value
        elif old_value is not None and new_value is None:
            changes_old[key] = "Removed from configuration"
        elif has_changes(old_value, new_value):
            changes_old[key] = old_value
            changes_new[key] = new_value

    return changes_old, changes_new
