import pytest

from extensions import utils


def test_check_gui_compatibility(mocker):
    # No traceback with compatible version

    version_path = "extensions.utils._get_karabo_gui_version"
    version = mocker.patch(version_path)
    version.return_value = utils.VERSION(2, 15)
    assert utils.requires_gui_version(2, 15) is None
    assert utils.requires_gui_version(2, 14) is None

    # Traceback when the module requires newer version than
    # current Karabo GUI version.
    with pytest.raises(utils.CompatibilityError):
        utils.requires_gui_version(2, 16)


def test_gui_version_compatible(mocker):
    version_path = "extensions.utils._get_karabo_gui_version"
    version = mocker.patch(version_path)
    version.return_value = utils.VERSION(2, 15)
    assert utils.gui_version_compatible(2, 15)

    assert not utils.gui_version_compatible(50, 12)
