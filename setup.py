from setuptools import find_packages, setup

setup(
    name='GUIExtensions',
    use_scm_version={'write_to': 'src/extensions/_version.py'},
    author='CAS',
    author_email='CAS',
    description='Widget extensions for KaraboGui',
    url='https://git.xfel.eu/gitlab/karaboDevices/guiextensions/',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    entry_points={
        'karabogui.gui_extensions': [
            'IPMQuadrant = extensions.display_ipm_quadrant',
            'ScatterPosition = extensions.display_scatter_position',
            'ScantoolDynamic = extensions.display_scantool_dynamic',
            'DynamicDigitizer = extensions.display_dynamic_digitizer',
            'PointAndClick = extensions.point_and_click',
            'DoocsMirrorTable = extensions.display_doocs_mirror_table',
            'DoocsLocationTable = extensions.display_doocs_location_table'
        ],
    },
    include_package_data=True,
)
