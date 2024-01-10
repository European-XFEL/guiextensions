# Karabacon-specific values
NR_VALUES = 6
NR_MOTORS = 4

# Karabacon node variables
SCAN_TYPE = "scanType"
VECTOR_DATA = "vectorData"
IS_VECTOR_DATA = "isVectorData"
STEPS = "steps"
ACTUAL_STEP = "actualStep"
CURRENT_INDEX = "currentIndex"
START_POSITIONS = "startPositions"
STOP_POSITIONS = "stopPositions"
POS = "pos"
Y = "y"
ALIGNER = "aligner"
MOTOR_NAMES = [f"pos{index}" for index in range(NR_MOTORS)]
SOURCE_NAMES = [f"y{index}" for index in range(NR_VALUES)]
TEST_MOTOR_IDS = [f"TEST/DEVICE/MOTOR{index}" for index in range(NR_MOTORS)]
TEST_SOURCE_IDS = [f"TEST/DEVICE/SOURCE{index}" for index in range(NR_VALUES)]

MOTORS = "motors"
SOURCES = "sources"
MOTOR_IDS = "motorIds"
SOURCE_IDS = "sourceIds"

TSCAN = "tscan"
CSCAN = "cscan"
MESHES = ["mesh", "dmesh"]

# Plot config keys
X_DATA = "x_data"
Y_DATA = "y_data"
Z_DATA = "z_data"

ADD = "add"
REMOVE = "remove"
REMOVE_ALL = "remove_all"

# default scan
ASCAN_CONFIG = {
    SCAN_TYPE: "ascan",
    MOTORS: MOTOR_NAMES,
    SOURCES: SOURCE_NAMES,
    MOTOR_IDS: MOTOR_NAMES,
    SOURCE_IDS: SOURCE_NAMES,
    STEPS: [5],
    ACTUAL_STEP: 0,
    CURRENT_INDEX: [0],
    START_POSITIONS: [0],
    STOP_POSITIONS: [10]}

BUTTON_DEV_DIALOG = "device_dialog"
BUTTON_SORT = "sort"
BUTTON_REMOVE_ALL = "remove_all"
