import enum

import pyqtgraph as pg
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy.QtCore import Qt
from qtpy.QtGui import QPen
from qtpy.QtWidgets import QGraphicsItem
from traits.api import Instance, List, WeakRef

from karabo.common.scenemodel.api import build_model_config
from karabogui.api import (
    BaseBindingController, KaraboLegend, KaraboPlotView, VectorNumberBinding,
    generate_down_sample, get_binding_array_value, get_binding_value,
    get_default_pen, get_view_range, make_brush, make_pen,
    register_binding_controller, with_display_type)

from .models.api import TriggerSliceGraphModel

REGION_ALPHA = 80


class Painter(enum.Enum):
    FEL_BRUSH = make_brush("b", alpha=REGION_ALPHA)
    PPL_BRUSH = make_brush("o", alpha=REGION_ALPHA)
    BOTH_BRUSH = make_brush("g", alpha=REGION_ALPHA)
    SEPARATOR_PEN = make_pen("r", alpha=REGION_ALPHA * 2)


class ColorBox(ItemSample):
    """The color box in the legend that shows the curve pen color"""

    def __init__(self, brush):
        super(ColorBox, self).__init__(item=None)
        self._brush = brush
        self._pen = QPen(Qt.NoPen)

    def paint(self, painter, *args):
        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawRect(0, 0, 10, 14)


@register_binding_controller(
    ui_name="Trigger Slice Graph",
    klassname="TriggerSliceGraph",
    binding_type=VectorNumberBinding,
    is_compatible=with_display_type("WidgetNode|TriggerSliceGraph"),
    priority=0,
    can_show_nothing=False,
)
class TriggerSliceGraph(BaseBindingController):
    model = Instance(TriggerSliceGraphModel, args=())

    _curve_item = WeakRef(QGraphicsItem)

    _trigger_regions = List(WeakRef(QGraphicsItem))
    _widget = WeakRef(KaraboPlotView)

    def create_widget(self, parent):
        self._widget = KaraboPlotView(parent=parent)
        self._widget.stateChanged.connect(self._change_model)
        self._widget.add_cross_target()
        self._widget.add_toolbar()
        self._widget.enable_export()

        # Add legend
        legend = KaraboLegend()
        legend.setParentItem(self._widget.plotItem.vb)
        legend.anchor(itemPos=(1, 1), parentPos=(1, 1), offset=(-5, -5))
        legend.addItem(ColorBox(Painter.FEL_BRUSH.value), name="FEL")
        legend.addItem(ColorBox(Painter.PPL_BRUSH.value), name="PPL")
        legend.addItem(ColorBox(Painter.BOTH_BRUSH.value), name="both")

        # Create curve item
        self._curve_item = self._widget.add_curve_item(pen=get_default_pen())

        # Finalize
        self._widget.restore(build_model_config(self.model))

        return self._widget

    def _add_trigger_region(self):
        item = pg.LinearRegionItem(pen=Painter.SEPARATOR_PEN.value,
                                   movable=False)
        self._widget.plotItem.addItem(item)
        self._trigger_regions.append(item)

    def value_update(self, proxy):
        binding = get_binding_value(proxy)
        if binding is None:
            return

        # Update plot (ignore timestamp)
        data, _ = get_binding_array_value(binding.data)
        if data is not None:
            rect = get_view_range(self._curve_item)
            x, y = generate_down_sample(data, rect=rect, deviation=True)
            self._curve_item.setData(x, y)
        else:
            self._curve_item.setData([], [])

        # Update trigger regions
        starts, _ = get_binding_array_value(binding.start)
        stops, _ = get_binding_array_value(binding.stop)
        fels, _ = get_binding_array_value(binding.fel)
        ppls, _ = get_binding_array_value(binding.ppl)

        if any(thing is None for thing in (starts, stops, fels, ppls)):
            return
        diff = len(starts) - len(self._trigger_regions)
        if diff > 0:
            for _ in range(diff):
                self._add_trigger_region()
        elif diff < 0:
            to_remove = self._trigger_regions[diff:]
            for region in to_remove:
                self._widget.plotItem.removeItem(region)
            self._trigger_regions = self._trigger_regions[:diff]

        for region, start, stop, fel, ppl in zip(
            self._trigger_regions, starts, stops, fels, ppls
        ):
            if fel and ppl:
                region.setBrush(Painter.BOTH_BRUSH.value)
            elif fel:
                region.setBrush(Painter.FEL_BRUSH.value)
            else:
                region.setBrush(Painter.PPL_BRUSH.value)
            region.setRegion((start, stop))

    # ----------------------------------------------------------------
    # Qt Slots

    def _change_model(self, content):
        self.model.trait_set(**content)
