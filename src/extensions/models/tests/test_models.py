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
    traits['x2_offset'] = 50.45
    traits['x2_step'] = 6.667
    traits['vline_visible'] = True
    traits['vline_value'] = -7.5675

    model = api.MetroSecAxisGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.x2_offset == 50.45
    assert read_model.x2_step == 6.667
    assert read_model.vline_visible is True
    assert read_model.vline_value == -7.5675


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


def test_special_column_table():
    traits = {"show_value": True, "value_is_percent": True,
              "color_by_value": False}
    model = api.SpecialColumnTableElementModel(**traits)
    read_model = single_model_round_trip(model)
    # FIXME: The geometry is not preserved in this widget
    # _assert_geometry_traits(read_model)
    assert read_model.show_value is True
    assert read_model.value_is_percent is True
    assert read_model.color_by_value is False


def test_historian_table_model():
    traits = _geometry_traits()
    model = api.HistorianTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_critical_compare_view():
    traits = _geometry_traits()
    model = api.CriticalCompareViewModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
