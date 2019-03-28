#############################################################################
# Author: <dennis.goeries@xfel.eu>
# Created on January 24, 2019
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################

from PyQt4.QtCore import Qt, QPoint, QRect
from PyQt4.QtGui import QColor, QLabel, QPainter, QPen
from traits.api import Instance

from karabogui.binding.api import WidgetNodeBinding
from karabogui.controllers.api import (
    BaseBindingController, register_binding_controller, with_display_type)

from .models.simple import IPMQuadrantModel

SILVER = QColor(192, 192, 192)
FIREBRICK = QColor(178, 34, 34)


def sign(value):
    return 1 if value >= 0 else -1


class Quadrant(QLabel):
    """The Quadrant widget can show X-ray beam positions

    All positions on a Quadrant are provided as normalized values between::

        -1 < x < 1
        -1 < y < 1

    According to a valid measure the quadrant is either painted red or gray.
    """

    def __init__(self, parent=None):
        super(Quadrant, self).__init__(parent)
        self.setMinimumSize(100, 100)

        self.gap_size_x = 0.2
        self.gap_size_y = 0.2
        self.diameter = 10
        self.beam_width = 1
        self.beam_height = 1

        # The beam positions
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.intensity = 0

    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        center = QPoint((width + 1) / 2, (height + 1) / 2)
        diameter = width - 2
        if height < width:
            diameter = height - 2
        # Normalization routine with respect to predefined settings!
        width_beam = diameter * (self.beam_width / self.diameter)
        height_beam = diameter * (self.beam_height / self.diameter)
        gap_width_x = diameter * (self.gap_size_x / self.diameter)
        gap_x = QRect(center.x() + 1 - gap_width_x / 2, center.y()
                      - diameter / 2, gap_width_x, diameter + 2)
        gap_width_y = diameter * (self.gap_size_y / self.diameter)
        gap_y = QRect(center.x() - 1 - diameter / 2, center.y() + 1
                      - gap_width_y / 2, diameter + 2, gap_width_y)
        pos_x = center.x() + self.pos_x * center.x() / 2
        pos_y = center.y() - self.pos_y * center.y() / 2

        with QPainter(self) as painter:
            # Draw the quadrant circle
            painter.setPen(QPen(SILVER))
            painter.setBrush(SILVER)
            painter.drawEllipse(center, diameter / 2, diameter / 2)
            # Make the gaps visible!
            painter.eraseRect(gap_x)
            painter.eraseRect(gap_y)
            if abs(self.pos_x) <= 1 and abs(self.pos_y) <= 1:
                painter.setPen(QPen(FIREBRICK))
                painter.setBrush(Qt.transparent)
                painter.drawEllipse(pos_x + 1 - width_beam / 2, pos_y + 1
                                    - height_beam / 2, width_beam, height_beam)

    def set_parameter(self, x, y, intensity):
        self.pos_x = x if abs(x) < 1 else sign(x)
        self.pos_y = y if abs(y) < 1 else sign(y)
        self.intensity = intensity


@register_binding_controller(
    ui_name='Quadrant-IPM Widget',
    klassname='IPM-Quadrant',
    binding_type=WidgetNodeBinding,
    is_compatible=with_display_type('WidgetNode|IPM-Quadrant'),
    priority=0, can_show_nothing=False)
class DisplayIPMQuadrant(BaseBindingController):
    """The IPM Quadrant widget is used to provide visual information

    It provides the latest beam positions in a quadrant like label. The latest
    updated beam position is shown with a red circle.
    """
    # The scene data model class for this controller
    model = Instance(IPMQuadrantModel, args=())

    def create_widget(self, parent):
        widget = Quadrant(parent)
        widget.setAlignment(Qt.AlignCenter)
        return widget

    def value_update(self, proxy):
        if proxy.value is None:
            return
        # NOTE: We utilize that all values are set at once in the pipeline!
        pos_x = proxy.value.posX.value
        pos_y = proxy.value.posY.value
        intensity = proxy.value.intensity.value
        self.widget.set_parameter(pos_x, pos_y, intensity)
        self.widget.update()
