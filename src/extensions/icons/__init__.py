import os.path as op

from qtpy.QtGui import QIcon


class Icon(object):
    """A lazy-loading class for QIcons

    QIcons can only be read once a QApplication is created. This
    class assures that icons are only loaded when needed."""
    def __init__(self, name):
        self.name = name
        self._icon = None

    @property
    def icon(self):
        if self._icon is None:
            self._icon = QIcon(op.join(op.dirname(__file__), self.name))
        return self._icon

    def __get__(self, instance, owner):
        return self.icon


deselect_all = Icon("deselect_all.svg")
invert_select = Icon("invert_select.svg")
select_all = Icon("select_all.svg")
crosshair_available = Icon("crosshair-available.svg")
runfile = Icon("run_file.svg")
thumbs_up = Icon("thumbs-up.svg")
thumbs_down = Icon("thumbs-down.svg")
