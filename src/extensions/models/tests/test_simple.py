from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api
from ..simple import _SIMPLE_WIDGET_MODELS
from .utils import _assert_geometry_traits, _geometry_traits


def test_ipm_quadrant_model():
    traits = _geometry_traits()
    model = api.IPMQuadrantModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)


def test_editable_text_options():
    traits = _geometry_traits()
    traits["strict"] = False
    model = api.EditableTextOptionsModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert not read_model.strict


def test_pnc_model():
    model = api.PointAndClickModel(klass="EditablePointAndClick")
    read_model = single_model_round_trip(model)
    assert read_model.klass == "EditablePointAndClick"

    model = api.PointAndClickModel(klass="DisplayPointAndClick")
    read_model = single_model_round_trip(model)
    assert read_model.klass == "DisplayPointAndClick"


def test_editable_datetime():
    traits = _geometry_traits()
    traits["time_format"] = "%H:%M"
    model = api.EditableDateTimeModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert model.time_format == "%H:%M"


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
        assert model.filterInstances[i].filter_text == filters[
            i].filter_text, msg  # noqa
        assert model.filterInstances[i].is_active == filters[i].is_active, msg


def test_simple_widgets():
    """Test that all simple widgets are provided in the model api and
    test their geometry
    """
    for name in _SIMPLE_WIDGET_MODELS:
        klass = getattr(api, name)
        traits = _geometry_traits()
        model = klass(**traits)
        read_model = single_model_round_trip(model)
        _assert_geometry_traits(read_model)
