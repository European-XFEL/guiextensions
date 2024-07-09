from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFrame, QHBoxLayout, QLabel, QSlider, QWidget
from traits.api import Instance

from karabogui.api import (
    BaseBindingController, SignalBlocker, VectorBinding, get_editor_value,
    register_binding_controller, with_display_type)

from .models.api import VectorSliderModel

WIDGET_HEIGHT = 20
WIDGET_WIDTH = 60


@register_binding_controller(ui_name='Vector Slider', can_edit=True,
                             klassname='VectorSlider',
                             binding_type=VectorBinding,
                             is_compatible=with_display_type('VectorSlider'))
class VectorSlider(BaseBindingController):
    # The scene model class for this controller
    model = Instance(VectorSliderModel, args=())

    slider = Instance(QSlider)
    label = Instance(QLabel)

    def create_widget(self, parent):
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        widget.setLayout(layout)

        self.slider = QSlider(Qt.Horizontal, widget)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.valueChanged.connect(self._edit_value)

        layout.addWidget(self.slider)

        self.label = QLabel(widget)
        self.label.setFrameStyle(QFrame.Box)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(WIDGET_WIDTH, WIDGET_HEIGHT)
        self.label.setStyleSheet("font: 6pt; font-weight: bold;")
        layout.addWidget(self.label)

        return widget

    def value_update(self, proxy):
        if proxy is self.proxy:
            image_number = get_editor_value(proxy)
            if image_number is not None:
                with SignalBlocker(self.slider):
                    self.slider.setRange(0, int(image_number[0] - 1))
                    self.slider.setValue(int(image_number[1]))
                    self.label.setText(str(image_number[1]))

    def _edit_value(self, value):
        self.proxy.edit_value = [self.slider.maximum() + 1, value]
        self.label.setText(str(value))
