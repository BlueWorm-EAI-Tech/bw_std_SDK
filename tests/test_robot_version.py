import json
from pathlib import Path
import sys
import time

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mantis import Mantis
from mantis.constants import (
    LEFT_ARM_URDF_JOINTS,
    RIGHT_ARM_URDF_JOINTS,
    URDF_ARM_JOINT_NAMES,
)


class _FakePublisher:
    def __init__(self):
        self.messages = []

    def put(self, payload):
        self.messages.append(payload)


def _make_connected_robot(robot_version="standard"):
    robot = Mantis(robot_version=robot_version)
    robot._connected = True
    return robot


def test_mantis_uses_standard_as_default_robot_version():
    robot = Mantis()

    assert robot._robot_version == "standard"


def test_mantis_accepts_std_alias():
    robot = Mantis(robot_version="std")

    assert robot._robot_version == "standard"


def test_mantis_repr_reports_standard_profile_without_removed_sim_state():
    robot = Mantis()

    assert repr(robot) == "Mantis(status='未连接', robot_version='standard')"


def test_mantis_does_not_expose_joint_direction_reference():
    robot_default = Mantis()
    robot_standard = Mantis(robot_version="standard")

    assert not hasattr(robot_default, "joint_direction_map")
    assert not hasattr(robot_standard, "joint_direction_map")


def test_mantis_rejects_unknown_robot_version():
    with pytest.raises(ValueError, match="robot_version"):
        Mantis(robot_version="3.0")


def test_publish_full_state_uses_raw_urdf_arm_angles():
    robot = Mantis()
    publisher = _FakePublisher()
    robot._publishers["joints"] = publisher
    robot.left_arm._positions = [0.1, 0.2, 0.3, -0.4, 0.5, -0.6, 0.7]
    robot.right_arm._positions = [-0.8, 0.9, -1.0, 1.1, -1.2, 1.3, -1.4]

    robot._publish_full_state()

    assert len(publisher.messages) == 1
    msg = json.loads(publisher.messages[0].decode("utf-8"))
    assert msg["name"][: len(URDF_ARM_JOINT_NAMES)] == list(URDF_ARM_JOINT_NAMES)
    assert msg["position"][: len(URDF_ARM_JOINT_NAMES)] == pytest.approx(
        robot.left_arm.positions + robot.right_arm.positions
    )


def test_head_publishes_pitch_yaw_and_roll_for_sdk_bridge():
    robot = _make_connected_robot()
    robot._publishers["joints"] = _FakePublisher()

    robot.head.set_pose(pitch=-0.1, yaw=0.2, roll=0.05, block=False)

    msg = json.loads(robot._publishers["joints"].messages[-1].decode("utf-8"))
    assert msg["name"] == ["Head_Joint", "Neck_Joint", "head_roll_joint"]
    assert msg["position"] == pytest.approx([-0.1, 0.2, 0.05])


def test_arm_ik_absolute_control_publishes_robot_side_pose_command():
    robot = _make_connected_robot()
    publisher = _FakePublisher()
    robot._publishers["arm_command"] = publisher

    robot.left_arm.ik(0.1, 0.2, 0.3, 0.0, 0.0, 0.0, block=False, abs=True)

    assert len(publisher.messages) == 1
    msg = json.loads(publisher.messages[0].decode("utf-8"))
    assert msg["command_type"] == "pose_abs"
    assert msg["side"] == "left"
    assert msg["command_id"].startswith("sdk-")
    assert msg["pose"] == {
        "x": pytest.approx(0.1),
        "y": pytest.approx(0.2),
        "z": pytest.approx(0.3),
        "roll": pytest.approx(0.0),
        "pitch": pytest.approx(0.0),
        "yaw": pytest.approx(0.0),
    }


def test_arm_ik_can_publish_motion_profile_override():
    robot = _make_connected_robot()
    publisher = _FakePublisher()
    robot._publishers["arm_command"] = publisher

    robot.left_arm.ik(
        0.1,
        0.2,
        0.3,
        0.0,
        0.0,
        0.0,
        block=False,
        abs=True,
        max_velocity=2.0,
        max_acceleration=4.0,
        max_jerk=8.0,
    )

    msg = json.loads(publisher.messages[0].decode("utf-8"))
    assert msg["motion_profile"] == {
        "max_velocity": pytest.approx(2.0),
        "max_acceleration": pytest.approx(4.0),
        "max_jerk": pytest.approx(8.0),
    }


def test_arm_ik_relative_control_publishes_robot_side_delta_command():
    robot = _make_connected_robot()
    publisher = _FakePublisher()
    robot._publishers["arm_command"] = publisher

    robot.right_arm.ik(0.01, -0.02, 0.03, 0.1, -0.2, 0.3, block=False, abs=False)

    assert len(publisher.messages) == 1
    msg = json.loads(publisher.messages[0].decode("utf-8"))
    assert msg["command_type"] == "pose_rel"
    assert msg["side"] == "right"
    assert msg["command_id"].startswith("sdk-")
    assert msg["delta"] == [
        pytest.approx(0.01),
        pytest.approx(-0.02),
        pytest.approx(0.03),
        pytest.approx(0.1),
        pytest.approx(-0.2),
        pytest.approx(0.3),
    ]


def test_arm_ik_block_true_waits_for_matching_command_status(monkeypatch):
    robot = _make_connected_robot()
    publisher = _FakePublisher()
    robot._publishers["arm_command"] = publisher
    waited_ids = []

    def fake_wait_command(command_id, **kwargs):
        waited_ids.append(command_id)

    monkeypatch.setattr(robot, "_wait_arm_command", fake_wait_command)
    robot.left_arm.ik(0.01, 0.0, 0.0, 0.0, 0.0, 0.0, block=True, abs=False)

    msg = json.loads(publisher.messages[0].decode("utf-8"))
    assert waited_ids == [msg["command_id"]]


def test_arm_ik_block_true_raises_failed_status(monkeypatch):
    robot = _make_connected_robot()
    robot._publishers["arm_command"] = _FakePublisher()

    def fake_wait_command(command_id, **kwargs):
        raise RuntimeError(f"SDK arm command {command_id} failed: IK solver failed")

    monkeypatch.setattr(robot, "_wait_arm_command", fake_wait_command)

    with pytest.raises(RuntimeError, match="IK solver failed"):
        robot.left_arm.ik(0.01, 0.0, 0.0, 0.0, 0.0, 0.0, block=True, abs=False)


def test_direct_arm_joint_control_uses_partial_standard_commands():
    robot = Mantis(robot_version="standard")
    robot._connected = True
    robot._publishers["arm_command"] = _FakePublisher()

    robot.left_arm.set_joint(0, 0.3, block=False)
    robot.right_arm.set_joints([0.1] * 7, block=False)

    assert robot.left_arm.positions[0] == 0.3
    assert robot.right_arm.positions == [0.1] * 7
    messages = [
        json.loads(payload.decode("utf-8"))
        for payload in robot._publishers["arm_command"].messages
    ]
    assert messages[-1]["command_type"] == "joint"
    assert messages[-1]["command_id"].startswith("sdk-")
    assert messages[0]["name"] == [LEFT_ARM_URDF_JOINTS[0]]
    assert messages[0]["position"] == [pytest.approx(0.3)]
    assert messages[-1]["name"] == list(RIGHT_ARM_URDF_JOINTS)
    assert messages[-1]["position"] == pytest.approx([0.1] * 7)


def test_direct_arm_joint_control_can_publish_motion_profile_override():
    robot = Mantis(robot_version="standard")
    robot._connected = True
    robot._publishers["arm_command"] = _FakePublisher()

    robot.left_arm.set_joint(
        0,
        0.3,
        block=False,
        max_velocity=1.5,
        max_acceleration=3.0,
        max_jerk=6.0,
    )

    msg = json.loads(robot._publishers["arm_command"].messages[-1].decode("utf-8"))
    assert msg["motion_profile"] == {
        "max_velocity": pytest.approx(1.5),
        "max_acceleration": pytest.approx(3.0),
        "max_jerk": pytest.approx(6.0),
    }


def test_arm_home_can_publish_motion_profile_override():
    robot = Mantis(robot_version="standard")
    robot._connected = True
    robot._publishers["arm_command"] = _FakePublisher()

    robot.left_arm.home(
        block=False,
        max_velocity=2.0,
        max_acceleration=4.0,
        max_jerk=8.0,
    )

    msg = json.loads(robot._publishers["arm_command"].messages[-1].decode("utf-8"))
    assert msg["command_type"] == "joint"
    assert msg["motion_profile"] == {
        "max_velocity": pytest.approx(2.0),
        "max_acceleration": pytest.approx(4.0),
        "max_jerk": pytest.approx(8.0),
    }


def test_standard_waist_bend_control_is_not_available():
    robot = Mantis(robot_version="standard")
    robot._connected = True

    for method, args in (
        (robot.waist.set_bend_speed, (0.25,)),
        (robot.waist.set_bend, (-0.4,)),
        (robot.waist.bend_forward, (0.2,)),
        (robot.waist.bend_backward, (0.1,)),
    ):
        with pytest.raises(NotImplementedError, match="Standard.*未提供.*兼容接口"):
            method(*args)


def test_waist_height_publishes_standard_pelvis_height_position_command():
    robot = Mantis(robot_version="standard")
    robot._connected = True
    robot._publishers["joints"] = _FakePublisher()
    robot._publishers["pelvis_height"] = _FakePublisher()

    robot.waist.set_speed(0.12)
    robot.waist.set_height(0.05, block=False)

    messages = [
        json.loads(payload.decode("utf-8"))
        for payload in robot._publishers["pelvis_height"].messages
    ]
    assert messages == [{"height": pytest.approx(0.05), "max_velocity": pytest.approx(0.12)}]


def test_wait_requires_fresh_stopped_status_samples_before_returning(monkeypatch):
    robot = Mantis(robot_version="standard")
    robot._connected = True
    robot._last_status_update_time = 0.0
    robot._system_status = {
        "motion_names": ["waist"],
        "motion_states": [0],
    }

    time_calls = []
    wait_calls = []

    def fake_time():
        time_calls.append(True)
        return 0.0 if len(time_calls) == 1 else 2.0

    def fake_sleep(duration):
        wait_calls.append(duration)
        if len(wait_calls) > 20:
            raise TimeoutError("wait kept polling for fresh stopped samples")

    monkeypatch.setattr(time, "time", fake_time)
    monkeypatch.setattr(time, "sleep", fake_sleep)

    with pytest.raises(TimeoutError):
        robot.wait(["waist"])
