import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONSTANTS_FILE = REPO_ROOT / "mantis" / "constants.py"


def _load_constants_module():
    spec = importlib.util.spec_from_file_location("mantis_constants", CONSTANTS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sdk_arm_limits_match_standard_runtime_urdf_ranges():
    constants = _load_constants_module()

    expected_left_limits = [
        (-2.069, 1.022),
        (-0.142, 2.077),
        (-1.541, 1.541),
        (-0.529, 1.355),
        (-1.540, 1.540),
        (-0.756, 0.756),
        (-1.017, 1.018),
    ]
    expected_right_limits = list(expected_left_limits)
    expected_right_limits[1] = (-2.077, 0.142)

    assert constants.LEFT_ARM_LIMITS == expected_left_limits
    assert constants.RIGHT_ARM_LIMITS == expected_right_limits


def test_sdk_public_joint_order_maps_directly_to_standard_degree_order():
    constants = _load_constants_module()

    assert constants.LEFT_ARM_JOINTS == [
        "left_shoulder_pitch_joint",
        "left_shoulder_roll_joint",
        "left_shoulder_yaw_joint",
        "left_elbow_pitch_joint",
        "left_wrist_roll_joint",
        "left_wrist_pitch_joint",
        "left_wrist_yaw_joint",
    ]
    assert constants.LEFT_ARM_URDF_JOINTS == [
        f"A_left_Degree{degree}_joint" for degree in range(1, 8)
    ]
    assert constants.RIGHT_ARM_URDF_JOINTS == [
        f"A_right_Degree{degree}_joint" for degree in range(1, 8)
    ]
    assert constants.SERIAL_TO_URDF_MAP == dict(
        zip(constants.JOINT_NAMES, constants.URDF_ARM_JOINT_NAMES)
    )


def test_standard_auxiliary_limits_are_exposed_in_sdk_units():
    constants = _load_constants_module()

    assert constants.HEAD_LIMITS == {
        "pitch": (-0.785, 0.524),
        "yaw": (-1.570, 1.570),
        "roll": (-0.349, 0.349),
    }
