from extensions.models.api import VectorLimitedDoubleLineEditModel
from karabo.common.scenemodel.tests.utils import (
    base_widget_traits, single_model_round_trip)


def test_limited_double_line_edit():
    traits = base_widget_traits()
    traits['decimals'] = 3
    model = VectorLimitedDoubleLineEditModel(**traits)
    assert model.parent_component == "EditableApplyLaterComponent"

    read_model = single_model_round_trip(model)
    assert read_model.decimals == 3
    assert read_model.parent_component == model.parent_component
