import pytest

from extensions.models.api import (
    DetectorCellsModel, LimitedDoubleLineEditModel, MultipleDetectorCellsModel,
    VectorLimitedDoubleLineEditModel)
from karabo.common.scenemodel.tests.utils import (
    base_widget_traits, single_model_round_trip)


def test_vector_limited_double_line_edit():
    traits = base_widget_traits()
    traits['decimals'] = 3
    model = VectorLimitedDoubleLineEditModel(**traits)
    assert model.parent_component == "EditableApplyLaterComponent"

    read_model = single_model_round_trip(model)
    assert read_model.decimals == 3
    assert read_model.parent_component == model.parent_component


def test_limited_double_line_edit():
    traits = base_widget_traits()
    traits['decimals'] = 2
    model = LimitedDoubleLineEditModel(**traits)
    assert model.parent_component == "EditableApplyLaterComponent"

    read_model = single_model_round_trip(model)
    assert read_model.decimals == 2
    assert read_model.parent_component == model.parent_component


@pytest.mark.parametrize("model_cls",
                         [DetectorCellsModel, MultipleDetectorCellsModel])
def test_detector_cells_widget(model_cls):
    traits = base_widget_traits()
    traits['rows'] = 40
    traits['columns'] = 20
    traits['legend_location'] = 'right'
    model = model_cls(**traits)

    read_model = single_model_round_trip(model)
    assert read_model.rows == 40
    assert read_model.columns == 20
    assert read_model.legend_location == 'right'
