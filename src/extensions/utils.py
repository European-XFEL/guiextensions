from collections import namedtuple

import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QPalette
from qtpy.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLineEdit, QStyledItemDelegate,
    QToolButton, QWidget)
from traits.api import Undefined

from karabo.native import Hash, Timestamp, Type, is_equal
from karabogui.api import (
    REFERENCE_TYPENUM_TO_DTYPE, ListEditDialog, NodeBinding, SignalBlocker,
    get_binding_value, get_editor_value, icons)

try:
    from karabogui.api import WIDGET_MIN_HEIGHT
except ImportError:
    from karabogui.const import WIDGET_MIN_HEIGHT

VERSION = namedtuple("VERSION", ["major", "minor"])


def get_array_data(binding, default=None):
    """Retrieve the array and timestamp data from a property proxy belonging
    to an array binding

    NOTE: This is entirely grabbed from karabogui since the original
    implementation accepts only the proxy (and not the binding). This doesn't
    work when the binding of interest is a node child.

    :param default: default value to be returned if no value is available

    This function checks for `Undefined` on the proxy value and `None` data.
    If not data is available the `default` is returned with actual timestamp.

    :returns: data, timestamp
    """
    if binding is None:
        return default, Timestamp()

    if binding.__class__.__name__.startswith('Vector'):
        value = binding.value
        if value is None or value is Undefined:
            return default, Timestamp()

        return value, binding.timestamp

    # We now have an `NDArray`
    node = binding.value
    if node is Undefined:
        return default, Timestamp()

    pixels = node.data.value
    if pixels is Undefined:
        return default, Timestamp()

    shape = node.shape.value
    arr_type = REFERENCE_TYPENUM_TO_DTYPE.get(node.type.value, 'float64')
    value = np.frombuffer(pixels, dtype=arr_type, count=shape.prod())
    value.shape = shape
    timestamp = node.data.timestamp
    # Note: Current traits always casts to 1dim
    return value, timestamp


def get_ndarray_hash_from_data(data, timestamp=None):
    attrs = {} if timestamp is None else timestamp.toDict()

    h = Hash()
    h.setElement("type", get_dtype(data.dtype), attrs)
    h.setElement("isBigEndian", data.dtype.str[0] == ">", attrs)
    h.setElement("shape", np.array(data.shape, dtype=np.uint64),
                 attrs)
    h.setElement("data", data.tobytes(), attrs)
    return h


def get_dtype(dtype):
    dstr = dtype.str
    if dstr not in Type.strs:
        dstr = dtype.newbyteorder().str

    return Type.strs[dstr].number


def get_node_value(proxy, *, key):
    node = proxy.value
    return None if node is Undefined else getattr(node, key, None)


def value_from_node(proxy, *, key):
    return get_binding_value(get_node_value(proxy, key=key))


def guess_path(proxy, *, klass, output=False, excluded=tuple()):
    proxy_node = get_binding_value(proxy)
    for proxy_name in proxy_node:
        # Inspect on the top level of widget node
        binding = getattr(proxy_node, proxy_name)
        if (not output
                and isinstance(binding, klass)
                and proxy_name not in excluded):
            return proxy_name

        # Inspect inside an output node
        if output and isinstance(binding, NodeBinding):
            output_node = get_binding_value(binding)
            for output_name in output_node:
                if output_name in ('path', 'trainId'):
                    continue
                binding = getattr(output_node, output_name)
                if isinstance(binding, klass) and proxy_name not in excluded:
                    return proxy_name

    return ''


def rotate_points(points, origin, angle):
    x_norm, y_norm = np.subtract(points, origin)
    sin, cos = np.sin(angle), np.cos(angle)

    x_rot = x_norm * cos - y_norm * sin
    y_rot = x_norm * sin + y_norm * cos

    return np.add((x_rot, y_rot), origin)


def reflect_angle(angle):
    """Reflect angle (in degrees) and normalize to range 0-180."""
    return 180 - (angle + 180) % 180


# -----------------------------------------------------------------------------
# Twin axis view box


class TwinXViewBox(pg.ViewBox):
    """ This is a non-reactive viewbox that is used to plot a second set of
    data points in a twinx plot."""

    def __init__(self, y_label=None, parent=None):
        super().__init__(parent=parent, enableMenu=False)
        self.setMouseEnabled(x=True, y=True)
        self.setZValue(10000)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.y_label = y_label

    def linkToPlotItem(self, plotItem):
        # Add to plot item
        plotItem.scene().addItem(self)
        viewBox = plotItem.getViewBox()
        viewBox.sigResized.connect(self._resize)
        viewBox.sigStateChanged.connect(self._view_changed)

        # Link to current axes
        axis = plotItem.getAxis('right')
        axis.linkToView(self)
        self.setXLink(viewBox)

        # Show y-axis ticks and labels
        axis.style["showValues"] = True
        axis.setStyle(**axis.axisStyle)
        axis.setLabel(text=self.y_label)

    @Slot(object)
    def _resize(self, main_viewBox):
        self.setGeometry(main_viewBox.sceneBoundingRect())

    @Slot(object)
    def _view_changed(self, main_viewBox):
        # We only care about `enableAutoRange` triggers
        enabled = main_viewBox.autoRangeEnabled()[1]
        self.enableAutoRange(1, enabled)

    def scaleBy(self, s=None, center=None, x=None, y=None):
        super().scaleBy(s=s, center=center, x=x, y=y)
        self.linkedView(0).scaleBy(s=s, x=x, y=y)


def add_twinx(plotItem, data_item=None, y_label=None):
    viewBox = TwinXViewBox(y_label=y_label)
    viewBox.linkToPlotItem(plotItem)
    if data_item is not None:
        viewBox.addItem(data_item)
    return viewBox


class CompatibilityError(RuntimeError):
    pass


class OptionsDelegate(QStyledItemDelegate):
    """Represents a combo box item in the table or tree.
    """

    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options
        self.tree = parent

    def createEditor(self, parent, option, index):
        """Reimplemented function of QStyledItemDelegate"""
        # This is specific for event condition tree
        item = self.tree.itemFromIndex(index)
        if not item.text(1):
            return
        editor = QComboBox(parent)
        editor.addItems(self.options)
        editor.setCurrentIndex(0)
        return editor

    def setModelData(self, editor, model, index):
        """Reimplemented function of QStyledItemDelegate"""
        old = index.model().data(index, Qt.DisplayRole)
        new = editor.currentText()
        if not is_equal(old, new):
            model.setData(index, new, Qt.EditRole)
            self.commitData.emit(self.sender())


class VectorDelegate(QStyledItemDelegate):
    """Represents vector item with linedit and button
    """

    def __init__(self, proxy, col, parent=None):
        super().__init__(parent)
        self.proxy = proxy
        self.col = col
        self.row = None
        self.last_cursor_position = 0
        self._internal_widget = None

    def createEditor(self, parent, option, index):
        widget = QWidget(parent)
        widget.setMinimumHeight(WIDGET_MIN_HEIGHT)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self._internal_widget = QLineEdit(parent)
        layout.addWidget(self._internal_widget)
        self._normal_palette = self._internal_widget.palette()
        self._error_palette = QPalette(self._normal_palette)
        self._error_palette.setColor(QPalette.Text, Qt.red)
        widget.setFocusProxy(self._internal_widget)

        self._internal_widget.textChanged.connect(self._on_user_edit)
        self._internal_widget.setFocusPolicy(Qt.StrongFocus)

        text = "Edit"
        edit_tb = QToolButton()
        edit_tb.setStatusTip(text)
        edit_tb.setToolTip(text)
        edit_tb.setIcon(icons.edit)
        edit_tb.setMinimumSize(WIDGET_MIN_HEIGHT, WIDGET_MIN_HEIGHT)
        edit_tb.setMaximumSize(25, 25)
        edit_tb.setFocusPolicy(Qt.NoFocus)
        edit_tb.clicked.connect(self._on_edit_clicked)
        layout.addWidget(edit_tb)

        self.row = self.parent().model().mapToSource(index).row()
        value = get_editor_value(self.proxy, [])
        # Extract data by column and row
        if value:
            value = value[self.row][f"{self.col}"]
        with SignalBlocker(self._internal_widget):
            self._internal_widget.setText(','.join(str(v) for v in value))
        self._internal_widget.setCursorPosition(self.last_cursor_position)

        return widget

    def _on_user_edit(self, text):
        if self.proxy.binding is None:
            return

        acceptable_input = self._internal_widget.hasAcceptableInput()
        self.last_cursor_position = self._internal_widget.cursorPosition()
        # update color after text change!
        palette = (self._normal_palette if acceptable_input
                   else self._error_palette)
        self._internal_widget.setPalette(palette)

    def setModelData(self, editor, model, index):
        """Reimplemented function of QStyledItemDelegate"""
        old = index.model().data(index, Qt.DisplayRole)
        new = self._internal_widget.text()
        if not is_equal(old, new):
            model.setData(index, new, Qt.EditRole)
            self.commitData.emit(self.sender())

    def _on_edit_clicked(self):
        if self.proxy.binding is None:
            return

        list_edit = ListEditDialog(self.proxy.binding, duplicates_ok=True,
                                   parent=self._internal_widget)

        values = get_editor_value(self.proxy, [])
        # Extract data by column and row
        if values:
            values = values[self.row][f"{self.col}"]

        list_edit.set_list(values)
        if list_edit.exec() == QDialog.Accepted:
            self.proxy.edit_value = list_edit.values
            with SignalBlocker(self._internal_widget):
                display = ','.join(str(v) for v in list_edit.values)
                self._internal_widget.setText(display)
            self._internal_widget.setCursorPosition(self.last_cursor_position)
        # Give back the focus!
        self._internal_widget.setFocus(Qt.PopupFocusReason)


def requires_gui_version(major: int, minor: int):
    """
    Check if the given version is older than the running Karabo GUI version.

    Raise a `CompatibilityError` if this is not the case

    :param major: integer to compare the major version
    :param minor: integer to compare the minor version
    """
    if not gui_version_compatible(major, minor):
        raise CompatibilityError(
            f"The KaraboGui of version {major}.{minor} or later is required")


def gui_version_compatible(major: int, minor: int) -> bool:
    """Check if we are compatible to a karabo gui version"""
    existing = _get_karabo_gui_version()
    compare = VERSION(major=major, minor=minor)
    return existing >= compare


def _get_karabo_gui_version():
    """
    Return the running Karabo GUI version as a named tuple.
    """
    try:
        from importlib_metadata import version
    except ModuleNotFoundError:
        # Python > 3.8
        from importlib.metadata import version

    gui_version = version("karabogui")
    major, minor = gui_version.split(".")[:2]
    try:
        return VERSION(major=int(major), minor=int(minor))
    except ValueError:
        # Happens in tests only ...
        return VERSION(major=3, minor=14)
