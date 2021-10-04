import numpy as np
from traits.api import Undefined

from karabo.native import Timestamp
from karabogui.binding.api import NodeBinding, get_binding_value

try:
    from karabogui.controllers.api import REFERENCE_TYPENUM_TO_DTYPE
except ImportError:
    from karabogui.binding.api import REFERENCE_TYPENUM_TO_DTYPE


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

    arr_type = REFERENCE_TYPENUM_TO_DTYPE.get(node.type.value, 'float64')
    value = np.frombuffer(pixels, dtype=arr_type)
    timestamp = node.data.timestamp
    # Note: Current traits always casts to 1dim
    if value.ndim == 1:
        return value, timestamp

    return default, Timestamp()


def get_node_value(proxy, *, key):
    node = proxy.value
    return None if node is Undefined else getattr(node, key, None)


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
