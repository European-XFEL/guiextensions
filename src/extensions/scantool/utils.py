from .const import NUM_MOTORS_TABLE


def get_num_motors(scan_type):
    return NUM_MOTORS_TABLE.get(scan_type, 0)
