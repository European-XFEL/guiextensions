from pathlib import Path
from time import time

from qtpy.QtCore import QTimer
from qtpy.QtSvg import QSvgWidget
from qtpy.QtWidgets import QAction, QInputDialog, QLabel, QWidget
from traits.api import Instance

from karabogui.api import (
    BaseBinding, BaseBindingController, NodeBinding, PropertyProxy,
    get_binding_value, register_binding_controller)

from .models.api import LiveDataIndicatorModel


def is_compatible(binding):
    return not isinstance(binding, NodeBinding)


PARENT_DIR = Path(__file__).parent
THUMBS_UP = str(Path(PARENT_DIR, "icons/thumbs-up.svg"))
THUMBS_DOWN = str(Path(PARENT_DIR, "icons/thumbs-down.svg"))


@register_binding_controller(ui_name="Live Data Indicator",
                             klassname="LiveDataIndicator",
                             binding_type=BaseBinding, priority=-30,
                             is_compatible=is_compatible,
                             can_show_nothing=False)
class LiveDataIndicator(BaseBindingController):

    model = Instance(LiveDataIndicatorModel, args=())
    _refresh_timer = Instance(QTimer)

    def create_widget(self, parent: QWidget) -> QLabel:
        widget = QSvgWidget(THUMBS_DOWN, parent=parent)
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._check_for_stale_data)

        update_interval = QAction("Update refresh interval...", widget)
        update_interval.triggered.connect(self._update_refresh_interval)
        widget.addAction(update_interval)

        return widget

    def value_update(self, proxy: PropertyProxy) -> None:
        if get_binding_value(proxy.binding) is None:
            return
        timestamp = proxy.binding.timestamp.time_sec
        if timestamp is not None:
            self.update_health_status(healthy=self._is_healthy())

        timeout = self.model.refresh_interval * 1000
        self._refresh_timer.start(timeout)

    def clear_widget(self) -> None:
        self.update_health_status(healthy=False)
        if self._refresh_timer.isActive():
            self._refresh_timer.stop()

    def update_health_status(self, healthy: bool) -> None:
        icon_path = THUMBS_UP if healthy else THUMBS_DOWN
        self.widget.load(icon_path)

    def _is_healthy(self) -> bool:
        timestamp = self.proxy.binding.timestamp.time_sec
        return (time() - timestamp) < self.model.refresh_interval

    def _check_for_stale_data(self) -> None:
        if not self._is_healthy():
            self.update_health_status(healthy=False)
            self._refresh_timer.stop()

    def _update_refresh_interval(self) -> None:
        value = self.model.refresh_interval
        interval, ok = QInputDialog.getInt(
            self.widget, "Refresh Interval", "Enter number", value=value,
            min=1)
        if ok:
            self.model.trait_set(refresh_interval=interval)
            self._refresh_timer.setInterval(interval*1000)
