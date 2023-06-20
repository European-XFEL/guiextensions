from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api
from .utils import _assert_geometry_traits, _geometry_traits


def test_scatter_position_model():
    traits = _geometry_traits()
    traits["x_label"] = "X"
    traits["y_label"] = "Y"
    traits["x_units"] = "XUNIT"
    traits["y_units"] = "YUNIT"
    traits["x_autorange"] = False
    traits["y_autorange"] = False
    traits["x_grid"] = True
    traits["y_grid"] = False
    traits["x_log"] = True
    traits["y_log"] = False
    traits["x_min"] = 0.1
    traits["x_max"] = 12.0
    traits["y_min"] = 0.2
    traits["y_max"] = 14.0
    traits["x_invert"] = True
    traits["y_invert"] = True
    # non generic
    traits["maxlen"] = 200
    traits["psize"] = 1.3

    model = api.ScatterPositionModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.x_label == "X"
    assert read_model.y_label == "Y"
    assert read_model.x_units == "XUNIT"
    assert read_model.y_units == "YUNIT"
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


def test_dynamic_graph():
    traits = _geometry_traits()
    traits["number"] = 30
    model = api.DynamicGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert model.number == 30


def test_xas_graph_model():
    traits = _geometry_traits()
    model = api.XasGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_table_vector_xy_model():
    traits = _geometry_traits()
    traits["legends"] = []
    model = api.TableVectorXYGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.legends == []


def test_extended_vector_xy_model():
    traits = _geometry_traits()
    traits["legends"] = []
    model = api.ExtendedVectorXYGraph(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.legends == []


def test_peak_integration_graph_model():
    traits = _geometry_traits()
    model = api.PeakIntegrationGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_vector_with_linear_regions_model():
    traits = _geometry_traits()
    model = api.VectorGraphWithLinearRegionsModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
