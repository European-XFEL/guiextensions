# Karabacon-specific values
NR_VALUES = 6
NR_MOTORS = 4

# Karabacon node variables
SCAN_TYPE = "scanType"
NUM_DATA_SOURCES = "numDataSources"
STEPS = "steps"
ACTUAL_STEP = "actualStep"
CURRENT_INDEX = "currentIndex"
START_POSITIONS = "startPositions"
STOP_POSITIONS = "stopPositions"
POS = "pos"
Y = "y"
MOTOR_NAMES = ["pos{}".format(index) for index in range(NR_MOTORS)]
SOURCE_NAMES = ["y{}".format(index) for index in range(NR_VALUES)]

# Scan types
ASCANS = ["ascan", "a2scan", "a3scan", "a4scan"]
DSCANS = ["dscan", "d2scan", "d3scan", "d4scan"]
CSCANS = ["cscan", "c2scan", "c3scan", "c4scan"]
MESHES = ["mesh", "dmesh"]

# Plot config keys
X_DATA = "x_data"
Y_DATA = "y_data"
Z_DATA = "z_data"

ADD = "add"
REMOVE = "remove"

# build {scan type: number of motors} lookup table
NUM_MOTORS_TABLE = {}
for index, motors in enumerate(zip(ASCANS, DSCANS, CSCANS), start=1):
    for motor in motors:
        NUM_MOTORS_TABLE[motor] = index

for mesh in MESHES:
    NUM_MOTORS_TABLE[mesh] = 2


# default scan
A4SCAN_CONFIG = {
    SCAN_TYPE: "a4scan",
    NUM_DATA_SOURCES: NR_VALUES,
    STEPS: [5],
    ACTUAL_STEP: 0,
    CURRENT_INDEX: [0],
    START_POSITIONS: [0],
    STOP_POSITIONS: [10]
}
