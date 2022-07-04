from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api


def _geometry_traits():
    return {'x': 0, 'y': 0, 'height': 100, 'width': 100}


def _assert_geometry_traits(model):
    traits = _geometry_traits()
    for name, value in traits.items():
        msg = "{} has the wrong value!".format(name)
        assert getattr(model, name) == value, msg


def test_vector_position_model():
    traits = _geometry_traits()
    traits['x_label'] = 'X'
    traits['y_label'] = 'Y'
    traits['x_units'] = 'XUNIT'
    traits['y_units'] = 'YUNIT'
    traits['x_autorange'] = False
    traits['y_autorange'] = False
    traits['x_grid'] = True
    traits['y_grid'] = False
    traits['x_log'] = True
    traits['y_log'] = False
    traits['x_min'] = 0.1
    traits['x_max'] = 12.0
    traits['y_min'] = 0.2
    traits['y_max'] = 14.0
    traits['x_invert'] = True
    traits['y_invert'] = True
    # non generic
    traits['maxlen'] = 200
    traits['psize'] = 1.3

    model = api.ScatterPositionModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.x_label == 'X'
    assert read_model.y_label == 'Y'
    assert read_model.x_units == 'XUNIT'
    assert read_model.y_units == 'YUNIT'
    assert read_model.x_autorange is False
    assert read_model.y_autorange is False
    assert read_model.x_grid is True
    assert read_model.y_grid is False
    assert read_model.x_log is True
    assert read_model.y_log is False
    assert read_model.x_min == 0.1
    assert read_model.x_max == 12.0
    assert read_model.y_min == 0.2
    assert read_model.y_max == 14.0
    assert read_model.x_invert is True
    assert read_model.y_invert is True
    assert read_model.maxlen == 200
    assert read_model.psize == 1.3


def test_ipm_quadrant_model():
    traits = _geometry_traits()
    model = api.IPMQuadrantModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_doocs_location_table_model():
    traits = _geometry_traits()

    model = api.DoocsLocationTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_doocs_mirror_table_model():
    traits = _geometry_traits()

    model = api.DoocsMirrorTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_pnc_model():
    model = api.PointAndClickModel(klass='EditablePointAndClick')
    read_model = single_model_round_trip(model)
    assert read_model.klass == 'EditablePointAndClick'


def test_metro_zone_plate_model():
    traits = _geometry_traits()
    model = api.MetroZonePlateModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_metro_xas_graph_model():
    traits = _geometry_traits()
    model = api.MetroXasGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_metro_secaxis_graph_model():
    traits = _geometry_traits()
    model = api.MetroSecAxisGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_metro_twinx_graph_model():
    traits = _geometry_traits()
    model = api.MetroTwinXGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_editable_datetime():
    traits = _geometry_traits()
    traits['time_format'] = "%H:%M"
    model = api.EditableDateTimeModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert model.time_format == "%H:%M"


def test_dynamic_graph():
    traits = _geometry_traits()
    traits['number'] = 30
    model = api.DynamicGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert model.number == 30


def test_critical_compare_view():
    traits = _geometry_traits()
    model = api.CriticalCompareViewModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_recovery_report_table_model():
    traits = _geometry_traits()

    model = api.RecoveryReportTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_selection_convenience_table_model():
    traits = _geometry_traits()
    model = api.SelectionTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_networkx_model():
    traits = _geometry_traits()
    positions = []
    filters = []
    for i in range(10):
        positions.append(api.NodePosition(device_id=f"foo{i}",
                                          x=i,
                                          y=-i))
        filters.append(api.FilterInstance(filter_text=f"bar{i}",
                                          is_active=(i % 2 == 0)))
    traits["nodePositions"] = positions
    traits["filterInstances"] = filters
    model = api.NetworkXModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)

    for i in range(10):
        msg = f"Node position does not match for {i}"
        assert model.nodePositions[i].device_id == positions[i].device_id, msg
        assert model.nodePositions[i].x == positions[i].x, msg
        assert model.nodePositions[i].y == positions[i].y, msg

        msg = f"Filter does not match for {i}"
        assert model.filterInstances[i].filter_text == filters[i].filter_text, msg  # noqa
        assert model.filterInstances[i].is_active == filters[i].is_active, msg
