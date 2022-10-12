from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api
from .utils import _assert_geometry_traits, _geometry_traits


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
