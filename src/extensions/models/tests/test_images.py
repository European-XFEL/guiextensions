from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api
from .utils import _assert_geometry_traits, _geometry_traits


def test_roi_annotate_model():
    traits = _geometry_traits()
    traits["colormap"] = "magma"
    model = api.ROIAnnotateModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    read_model.colormap = "magma"


def test_rect_roi_model():
    traits = _geometry_traits()
    model = api.RectRoiGraphModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
