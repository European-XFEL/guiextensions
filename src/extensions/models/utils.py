from karabo.common.scenemodel.api import (
    read_axes_set, read_basic_label, read_range_set, write_axes_set,
    write_basic_label, write_range_set)
from karabo.common.scenemodel.const import NS_KARABO
from karabo.common.scenemodel.io_utils import (
    read_base_widget_data, write_base_widget_data)


# Lifted from karabo.common.scenemodel.widget.graph_utils.py
def read_view_set(element):
    traits = {}
    traits["title"] = element.get(NS_KARABO + "title", "")
    traits["background"] = element.get(NS_KARABO + "background", "transparent")
    return traits


def write_view_set(model, element):
    element.set(NS_KARABO + "title", str(model.title))
    element.set(NS_KARABO + "background", str(model.background))


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


def update_base_table(element):
    """Return the base table properties from `element`"""
    traits = {}
    resizeToContents = element.get(NS_KARABO + "resizeToContents", "")
    resizeToContents = resizeToContents.lower() == "true"
    traits["resizeToContents"] = resizeToContents
    return traits


def update_filter_table(element):
    """Return the base filter table properties from `element`"""
    traits = update_base_table(element)
    sortingEnabled = element.get(NS_KARABO + "sortingEnabled", "")
    sortingEnabled = sortingEnabled.lower() == "true"
    traits["sortingEnabled"] = sortingEnabled
    # Filter Column
    filterKeyColumn = int(element.get(NS_KARABO + "filterKeyColumn", 0))
    traits["filterKeyColumn"] = filterKeyColumn
    return traits


def write_base_table(model, element):
    """Write the base table properties from `model` to `element`"""
    resizeToContents = str(model.resizeToContents).lower()
    element.set(NS_KARABO + "resizeToContents", resizeToContents)


def write_filter_table(model, element):
    """Write the basic filter table properties from `model` to `element`"""
    write_base_table(model, element)
    sortingEnabled = str(model.sortingEnabled).lower()
    element.set(NS_KARABO + "sortingEnabled", sortingEnabled)
    element.set(NS_KARABO + "filterKeyColumn", str(model.filterKeyColumn))
