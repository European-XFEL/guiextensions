from qtpy.QtCore import Qt

from karabogui.conftest import gui_app

from ..selection_dialog import SelectionDialog


def test_selection_dialog(gui_app: gui_app):
    devices = ["A", "B", "C"]
    excluded = ["A"]
    dialog = SelectionDialog(devices, excluded)

    model = dialog.table_view.model()
    assert model.rowCount() == 3
    item = model.item(0, 0)
    assert not item.checkState()
    item = model.item(0, 1)
    assert item.data(Qt.UserRole) == "A"
    item = model.item(1, 0)
    assert item.checkState()
    item = model.item(2, 0)
    assert item.checkState()
    assert dialog.devices == ["A"]
    item.setCheckState(False)
    assert dialog.devices == ["A", "C"]

    dialog.on_de_select_all()
    assert dialog.devices == ["A", "B", "C"]
