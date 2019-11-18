from traits.api import Dict, HasStrictTraits, List


class ItemRegistry(HasStrictTraits):

    _items = Dict()
    _unused = List

    def add(self, item, scan_config):
        # item is a PlotDataItem, scan_config is a dictionary of params:scans
        self._items[item] = scan_config

    def remove(self, item):
        if item in self._items:
            self._items.pop(item)
            if item not in self._unused:
                self._unused.append(item)

    def get_item_by_config(self, config):
        """Since config is considered as unique, this only returns one item"""
        for item, scan_config in self._items.items():
            if config == scan_config:
                return item

    def get_items_by_device(self, device):
        """Gets the items and consequent configs relevant to the device.
           Returns a dictionary of {item:config}"""
        to_update = {}
        for item, config in self._items.items():
            if device in config.values():
                if item not in to_update:
                    to_update[item] = config

        return to_update

    def has_unused(self):
        return len(self._unused) > 0

    def use(self, name):
        # Check if there's an item hooked in a name.
        # This is to preserve assigned color
        for item in self._unused:
            if item.opts['name'] == name:
                return item

        # Else, use first item and rename to corresponding name
        item = self._unused.pop(0)
        item.opts['name'] = name
        return item

    def used(self):
        return list(self._items.keys())
