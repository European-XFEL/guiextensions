from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api
from .utils import _assert_geometry_traits, _geometry_traits


def test_detector_module_selection_run_assistant():
    traits = _geometry_traits()
    traits['detector'] = "MID: AGIPD1M"

    model = api.RunAssistantModuleSelectionModel(**traits)
    read_model = single_model_round_trip(model)

    _assert_geometry_traits(read_model)
    assert read_model.detector == "MID: AGIPD1M"
