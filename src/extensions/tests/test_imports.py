from functools import partial

import extensions as gui_pkg
from karabo.testing.import_checker import (
    check_for_disallowed_module_imports, check_for_star_imports,
    run_checker_on_package)


def test_no_star_imports():
    """Scream bloody murder if there are ever star imports in the extensions"""
    run_checker_on_package(gui_pkg, check_for_star_imports)


def test_forbidden_imports():
    """Test forbidden imports in the gui extensions"""
    for forbidden in ("karabo.middlelayer", "karabo.middlelayer_api",
                      "PyQt5", "PyQt6", "PySide", "PySide2"):
        checker = partial(check_for_disallowed_module_imports, forbidden)
        run_checker_on_package(gui_pkg, checker)
