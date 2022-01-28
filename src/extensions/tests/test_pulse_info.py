from functools import reduce

import numpy as np

from karabo.native import AccessMode, Configurable, Hash, Node, VectorBool
from karabogui.testing import (
    GuiTestCase, get_class_property_proxy, set_proxy_hash)

from ..display_pulse_info import (
    BRUSH_EMPTY, BRUSH_FEL, PEN_DET, PEN_EMPTY, PulseIdMap, PulsePattern)


class PINode(Configurable):
    displayType = "WidgetNode|PulseId-Map"

    fel = VectorBool(displayedName="FEL Pulses",
                     accessMode=AccessMode.READONLY,
                     defaultValue=[])

    ppl = VectorBool(displayedName="PPL Pulses",
                     accessMode=AccessMode.READONLY,
                     defaultValue=[])

    det = VectorBool(displayedName="Detector Pulses",
                     accessMode=AccessMode.READONLY,
                     defaultValue=[])


class Object(Configurable):
    node = Node(PINode)


class TestWidgetNode(GuiTestCase):
    def setUp(self):
        super(TestWidgetNode, self).setUp()

        schema = Object.getClassSchema()
        self.proxy = get_class_property_proxy(schema, 'node')
        self.controller = PulseIdMap(proxy=self.proxy)
        self.controller.create(None)

    def tearDown(self):
        self.controller.destroy()
        assert self.controller.widget is None

    def test_values(self):
        fel = np.random.randint(0, 1, size=(2700,), dtype=np.bool_)
        ppl = np.random.randint(0, 1, size=(2700,), dtype=np.bool_)
        det = np.random.randint(0, 1, size=(2700,), dtype=np.bool_)

        set_proxy_hash(
            self.proxy,
            Hash('node.fel', fel,
                 'node.ppl', ppl,
                 'node.det', det)
        )
        np.testing.assert_array_equal(self.controller.widget.fel, fel)
        np.testing.assert_array_equal(self.controller.widget.ppl, ppl)
        np.testing.assert_array_equal(self.controller.widget.det, det)

    def test_colors(self):
        fel, ppl = self.controller.widget.pulses[0]
        self.assertEqual(fel.pen(), PEN_EMPTY)
        self.assertEqual(fel.brush(), BRUSH_EMPTY)
        self.assertEqual(ppl.isVisible(), False)

        self.proxy.value.fel.value = np.ones(2700, dtype=np.bool_)
        self.proxy.value.ppl.value = np.ones(2700, dtype=np.bool_)
        self.proxy.value.det.value = np.ones(2700, dtype=np.bool_)

        self.controller.value_update(self.proxy)

        fel, ppl = self.controller.widget.pulses[0]
        self.assertEqual(fel.pen(), PEN_DET)
        self.assertEqual(fel.brush(), BRUSH_FEL)
        self.assertEqual(ppl.isVisible(), True)


# -----------------------------------------------------------------------------

FEL = np.array([1202, 1282, 1362, 1442, 1522, 1602, 1682, 1762, 1842, 1922,
                2002, 2082, 2162, 2242, 2322])
PPL = np.array([1202, 1242, 1282, 1322, 1362, 1402, 1442, 1482, 1522, 1562,
                1602, 1642, 1682, 1722, 1762, 1802, 1842, 1882, 1922, 1962,
                2002, 2042, 2082, 2122, 2162, 2202, 2242, 2282, 2322, 2362])
DET = np.array([1202, 1242, 1282, 1322, 1362, 1402, 1442, 1482, 1522, 1562,
                1602, 1642, 1682, 1722, 1762, 1802, 1842, 1882, 1922, 1962,
                2002, 2042, 2082, 2122, 2162, 2202, 2242, 2282, 2322, 2362])


def test_pulse_pattern():
    # Setup mocks
    grid_calls = 0

    def grid_change(object, name, old, new):
        nonlocal grid_calls
        grid_calls += 1

    diff_calls = 0

    def diff_change():
        nonlocal diff_calls
        diff_calls += 1

    # Setup pattern controller and mocks
    pattern = PulsePattern()
    pattern.on_trait_change(grid_change, 'grid')
    pattern.on_trait_change(diff_change, 'diff')

    # --- First update: valid pulses
    grid_calls, diff_calls = 0, 0
    proxy = _create_proxy(fel=FEL, ppl=PPL, det=DET)
    pattern.set_node(proxy.value)

    grid = pattern.grid
    assert grid.shape == (31, 40)
    assert (grid.min(), grid.max()) == (1160, 2399)
    np.testing.assert_array_equal(pattern.diff,
                                  reduce(np.union1d, (FEL, PPL, DET)))
    assert grid_calls == 1
    assert diff_calls == 1

    # --- Second update: valid pulses, but duplicate of the previous call
    grid_calls, diff_calls = 0, 0
    proxy = _create_proxy(fel=FEL, ppl=PPL, det=DET)
    pattern.set_node(proxy.value)

    grid = pattern.grid
    assert grid.shape == (31, 40)
    assert (grid.min(), grid.max()) == (1160, 2399)
    np.testing.assert_array_equal(pattern.diff,
                                  reduce(np.union1d, (FEL, PPL, DET)))
    assert grid_calls == 0  # changes are not called
    assert diff_calls == 0

    # --- Third update: valid pulses, but everything is offseted by +1
    grid_calls, diff_calls = 0, 0
    prev_fel, prev_ppl, prev_det = (pattern.fel_index,
                                    pattern.ppl_index,
                                    pattern.det_index)
    offset = 1
    proxy = _create_proxy(fel=FEL + offset, ppl=PPL + offset, det=DET + offset)
    pattern.set_node(proxy.value)

    grid = pattern.grid
    assert grid.shape == (31, 40)
    assert (grid.min(), grid.max()) == (1160, 2399)
    previous_index = reduce(np.union1d, (prev_fel, prev_ppl, prev_det))
    current_index = reduce(np.union1d, (FEL, PPL, DET)) + offset
    changes = np.sort(np.hstack((previous_index, current_index)))
    np.testing.assert_array_equal(pattern.diff, changes)
    assert grid_calls == 0
    assert diff_calls == 1

    # --- Fourth update: valid pulses, but everything is offseted by -4
    grid_calls, diff_calls = 0, 0
    prev_fel, prev_ppl, prev_det = (pattern.fel_index,
                                    pattern.ppl_index,
                                    pattern.det_index)
    offset = -4
    proxy = _create_proxy(fel=FEL + offset, ppl=PPL + offset, det=DET + offset)
    pattern.set_node(proxy.value)

    grid = pattern.grid
    assert grid.shape == (31, 40)
    assert (grid.min(), grid.max()) == (1160, 2399)
    previous_index = reduce(np.union1d, (prev_fel, prev_ppl, prev_det))
    current_index = reduce(np.union1d, (FEL, PPL, DET)) + offset
    changes = np.sort(np.hstack((previous_index, current_index)))
    np.testing.assert_array_equal(pattern.diff, changes)
    assert grid_calls == 0
    assert diff_calls == 1


def _create_proxy(fel=None, ppl=None, det=None):
    schema = Object.getClassSchema()
    proxy = get_class_property_proxy(schema, 'node')

    fel_pattern = np.zeros(2700, dtype=np.bool_)
    fel_pattern[fel] = True
    proxy.value.fel.value = fel_pattern

    ppl_pattern = np.zeros(2700, dtype=np.bool_)
    ppl_pattern[ppl] = True
    proxy.value.ppl.value = ppl_pattern

    det_pattern = np.zeros(2700, dtype=np.bool_)
    det_pattern[det] = True
    proxy.value.det.value = det_pattern

    return proxy
