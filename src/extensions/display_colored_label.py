from urllib.parse import parse_qs

from qtpy.QtGui import QColor
from traits.api import Dict, Instance, String, Tuple

from karabogui.api import StringBinding, register_binding_controller
from karabogui.controllers.api import BaseLabelController

from .models.api import ColoredLabelModel


def is_compatible(binding):
    return "ColoredLabel" in binding.display_type


def create_colors(display_string):
    """Converts display_type string to color map dictionary.
    """
    def color_to_rgb(color_string):
        try:
            color = QColor(color_string)
        except Exception:
            return

        return color.red(), color.green(), color.blue(), color.alpha()

    query_colors = display_string.split("|")
    if not len(query_colors) == 2:
        return None, {}

    parsed = parse_qs(query_colors[1], keep_blank_values=True)
    color_map = {name: color[0] for name, color in parsed.items()}
    colors = {text: color_to_rgb(color) for text, color
              in color_map.items()}
    return colors


@register_binding_controller(ui_name="Colored Label",
                             klassname="ColoredLabel",
                             binding_type=StringBinding,
                             can_edit=False, priority=-100,
                             is_compatible=is_compatible,
                             can_show_nothing=False)
class ColoredLabel(BaseLabelController):
    model = Instance(ColoredLabelModel, args=())
    color_map = Dict(String, Tuple)

    def value_update(self, proxy):
        if proxy is self.proxy:
            super().value_update(proxy)

        color = self.color_map.get(proxy.value)
        if color is None:
            color = self.color_map.get("default")
        sheet = self.style_sheet.format(color)
        self.widget.setStyleSheet(sheet)

    def binding_update(self, proxy):
        """We received a binding_update and know about the attributes"""
        if proxy is self.proxy:
            self.color_map = create_colors(proxy.binding.display_type)
