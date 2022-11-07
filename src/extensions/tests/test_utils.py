import pytest

from extensions import utils


def test_check_gui_compatibility():
    # No traceback with compatible version
    assert utils.check_gui_compat(2, 15) is None

    # Traceback when the module requires newer version than
    # current Karabo GUI version.
    with pytest.raises(utils.CompatibilityError):
        utils.check_gui_compat(50, 12)


def test_get_gui_version():
    from karabogui._version import version_tuple

    major, minor, _, _ = version_tuple
    version = utils.get_gui_version()
    assert version.major == major
    assert version.minor == minor
