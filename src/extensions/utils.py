from karabogui.binding.api import get_binding_value, NodeBinding


def get_node_value(proxy, path):
    return get_binding_value(getattr(proxy.value, path))


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
