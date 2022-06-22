from setuptools import find_packages, setup

entries = {
    'karabogui.gui_extensions': [
        'CriticalCompareView = extensions.display_critical_compare_view',
        'BeamGraph = extensions.display_beam_graph',
        'DateTimeEdit = extensions.edit_datetime_label',
        'DoocsMirrorTable = extensions.display_doocs_mirror_table',
        'DoocsLocationTable = extensions.display_doocs_location_table',
        'DynamicDigitizer = extensions.display_dynamic_digitizer',
        'DynamicGraph = extensions.display_dynamic_graph',
        'ExtendedVectorXYGraph = extensions.display_extended_vector_xy_graph',
        'IPMQuadrant = extensions.display_ipm_quadrant',
        'MetroZonePlate = extensions.metro.zone_plate',
        'MetroXasGraph = extensions.metro.xas_graph',
        'MetroSecAxisGraph = extensions.metro.secaxis_graph',
        'MetroTwinXGraph = extensions.metro.twinx_graph',
        'NetworkX = extensions.display_networkx',
        'PointAndClick = extensions.point_and_click',
        'PulseIdMap = extensions.display_pulse_info',
        'RecoveryReportTable = extensions.display_recovery_report_table',
        'RoiGraph = extensions.display_roi_graph',
        'ScatterPosition = extensions.display_scatter_position',
        'ScantoolDynamic = extensions.display_scantool_dynamic',
        'SelectionTable = extensions.edit_selection_table',
        'StateAwareComponentManager = extensions.stateaware_component_manager',
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
