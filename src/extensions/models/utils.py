from karabo.common.scenemodel.api import (
    read_axes_set, read_basic_label, read_range_set, write_axes_set,
    write_basic_label, write_range_set)
from karabo.common.scenemodel.const import NS_KARABO
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)


# Lifted from karabo.common.scenemodel.widget.graph_utils.py
def read_view_set(element):
    traits = {}
    traits['title'] = element.get(NS_KARABO + 'title', '')
    traits['background'] = element.get(NS_KARABO + 'background', 'transparent')
    return traits


def write_view_set(model, element):
    element.set(NS_KARABO + 'title', str(model.title))
    element.set(NS_KARABO + 'background', str(model.background))


# Lifted from karabo.common.scenemodel.widget.graph_plots.py
def read_base_plot(element):
    """Read the base of all graph plots"""
    traits = read_base_widget_data(element)
    traits.update(read_basic_label(element))
    traits.update(read_axes_set(element))
    traits.update(read_range_set(element))
    traits.update(read_view_set(element))
    return traits


def write_base_plot(model, element, klass):
    """Write the base of all graph plots

    This method writes axes, labels, ranges and view (background, title) to
    the element.
    """
    write_base_widget_data(model, element, klass)
    write_basic_label(model, element)
    write_axes_set(model, element)
    write_range_set(model, element)
    write_view_set(model, element)
