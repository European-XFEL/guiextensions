#############################################################################
# Copyright (C) European XFEL GmbH Schenefeld. All rights reserved.
#############################################################################
from qtpy.QtCore import QModelIndex
from traits.api import Instance

from karabo.native import Timestamp
from karabogui.api import (
    BaseFilterTableController, VectorHashBinding, get_editor_value,
    register_binding_controller, with_display_type)

from ..models.api import ActiveEventsTableModel


def human_readable_time(timestamp):
    '''
    Return a timestamp in human readable format "YYYY-MM-DD, hh:mm:ss"
    '''
    return Timestamp(timestamp).toLocal().split(".")[0].replace('T', ', ')


@register_binding_controller(
    ui_name="Active Events Table",
    klassname="ActiveEventsTable",
    binding_type=VectorHashBinding,
    is_compatible=with_display_type("ActiveEventsTable"),
    can_edit=False, can_show_nothing=True)
class ActiveEventsTable(BaseFilterTableController):
    model = Instance(ActiveEventsTableModel, args=())

    def value_update(self, proxy):
        value = get_editor_value(proxy, [])
        if not value:
            self._item_model.clear_model()
            return

        # Remove or add rows if necessary
        row_count = self._item_model.rowCount()
        if row_count > len(value):
            start = len(value) - 1
            count = row_count - len(value)
            self._item_model.removeRows(start, count, QModelIndex(),
                                        from_device=True)
        elif row_count < len(value):
            start = row_count
            count = len(value) - row_count
            self._item_model.insertRows(start, count, QModelIndex(),
                                        from_device=True)

        table_value = []
        for row in value:
            row["timestamp"] = human_readable_time(row["timestamp"])
            table_value.append(row)
        self._item_model.updateData(value)
