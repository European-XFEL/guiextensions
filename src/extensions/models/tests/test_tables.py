from karabo.common.scenemodel.tests.utils import single_model_round_trip

from .. import api
from .utils import _assert_geometry_traits, _geometry_traits


def test_doocs_location_table_model():
    traits = _geometry_traits()
    traits["resizeToContents"] = True
    model = api.DoocsLocationTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.resizeToContents


def test_doocs_mirror_table_model():
    traits = _geometry_traits()
    traits["resizeToContents"] = True
    model = api.DoocsMirrorTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.resizeToContents


def test_critical_compare_view():
    traits = _geometry_traits()
    traits["resizeToContents"] = True
    model = api.CriticalCompareViewModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.resizeToContents


def test_recovery_report_table_model():
    traits = _geometry_traits()
    traits["resizeToContents"] = True
    model = api.RecoveryReportTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.resizeToContents


def test_motor_assignment_table():
    traits = _geometry_traits()
    traits["resizeToContents"] = True
    model = api.MotorAssignmentTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.resizeToContents


def test_selection_convenience_table_model():
    traits = _geometry_traits()
    traits["resizeToContents"] = True
    traits["filterKeyColumn"] = 1
    traits["sortingEnabled"] = True
    model = api.SelectionTableModel(**traits)
    read_model = single_model_round_trip(model)
    _assert_geometry_traits(read_model)
    assert read_model.resizeToContents
    assert read_model.filterKeyColumn == 1
    assert read_model.sortingEnabled
