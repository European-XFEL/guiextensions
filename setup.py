from setuptools import find_packages, setup

entries = {
    'karabogui.gui_extensions': [
        'Amore = extensions.amore.display_roi_annotate',
        'BeamGraph = extensions.display_beam_graph',
        'ConditionCommand = extensions.display_condition',
        'DateTimeEdit = extensions.edit_datetime_label',
        'DetectorCells = extensions.display_detector_cells',
        'DeviceReconfigurationTable = extensions.display_device_reconfiguration_table',  # noqa
        'DoocsMirrorTable = extensions.display_doocs_mirror_table',
        'DoocsLocationTable = extensions.display_doocs_location_table',
        'DynamicDigitizer = extensions.display_dynamic_digitizer',
        'DynamicGraph = extensions.display_dynamic_graph',
        'ExtendedVectorXYGraph = extensions.display_extended_vector_xy_graph',
        'EditableTextOptions = extensions.edit_text_options',
        'IPMQuadrant = extensions.display_ipm_quadrant',
        'ImageCrossHairGraph = extensions.display_image_crosshair_graph',
        'VectorLimitedDoubleLineEdit = extensions.edit_limited_lineedit',
        'VectorLimitedIntLineEdit = extensions.edit_limited_lineedit',
        'LimitedDoubleLineEdit = extensions.edit_limited_lineedit',
        'LimitedIntLineEdit = extensions.edit_limited_lineedit',
        'MetroZonePlate = extensions.metro.zone_plate',
        'MetroXasGraph = extensions.metro.xas_graph',
        'MetroSecAxisGraph = extensions.metro.secaxis_graph',
        'MetroTwinXGraph = extensions.metro.twinx_graph',
        'MotorStageAssignmentTable = extensions.edit_motor_stage_table',
        'NetworkX = extensions.display_networkx',
        'PeakIntegrationGraph = extensions.peak_integration_graph',
        'PointAndClick = extensions.point_and_click',
        'PulseIdMap = extensions.display_pulse_info',
        'RecoveryCompareView = extensions.display_recovery_compare_view',
        'RectRoiGraph = extensions.roi_graph',
        'ScatterPosition = extensions.display_scatter_position',
        'ScantoolDynamic = extensions.display_scantool_dynamic',
        'ScantoolDeviceView = extensions.display_scantool_device_view',
        'ScantoolTemplates = extensions.edit_scantool_templates',
        'SelectionTable = extensions.edit_selection_table',
        'StateAwareComponentManager = extensions.stateaware_component_manager',
        'XasGraph = extensions.display_xas_graph',
    ],
}

setup(
    name='GUIExtensions',
    use_scm_version={'write_to': 'src/extensions/_version.py'},
    author='CAS',
    author_email='CAS',
    description='Widget extensions for KaraboGui',
    url='https://git.xfel.eu/gitlab/karaboDevices/guiextensions/',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    entry_points=entries,
    include_package_data=True,
    package_data={
        "extensions": ["dialogs/ui/*.ui", "icons/*.svg"],
    }
)
