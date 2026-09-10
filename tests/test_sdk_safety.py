import importlib
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mantis import Mantis
from mantis.chassis import Chassis


class _FakeResource:
    def __init__(self):
        self.closed = False

    def undeclare(self):
        self.closed = True


class _FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class _FakeRobot:
    def __init__(self):
        self.commands = []
        self.wait_calls = []

    def _publish_chassis(self):
        self.commands.append((self.chassis._vx, self.chassis._vy, self.chassis._omega))

    def wait(self, names):
        self.wait_calls.append(list(names))

    def is_moving(self, _names):
        return False


def test_repeated_connect_is_idempotent_and_does_not_home(monkeypatch):
    robot = Mantis(ip="192.168.50.170", sn="BW_TEST")
    robot._connected = True
    robot._robot_ip = "192.168.50.170"
    robot._robot_sn = "BW_TEST"

    monkeypatch.setattr(robot, "home", lambda *args, **kwargs: pytest.fail("unexpected home"))

    assert robot.connect(ip="192.168.50.170", sn="BW_TEST") is True
    assert robot.is_connected is True


def test_failed_identity_resolution_closes_transport(monkeypatch):
    mantis_module = importlib.import_module("mantis.mantis")
    session = _FakeSession()
    robot = Mantis(ip="192.168.50.170")

    monkeypatch.setattr(mantis_module.zenoh, "open", lambda _config: session)
    monkeypatch.setattr(robot, "_resolve_identity", lambda **_kwargs: None)

    assert robot.connect(timeout=0.01) is False
    assert session.closed is True
    assert robot._session is None
    assert robot._publishers == {}


def test_close_transport_releases_resources_and_marks_disconnected():
    robot = Mantis()
    session = _FakeSession()
    publisher = _FakeResource()
    subscriber = _FakeResource()
    robot._session = session
    robot._publishers["test"] = publisher
    robot._subscribers["test"] = subscriber
    robot._connected = True

    robot._close_transport()

    assert session.closed is True
    assert publisher.closed is True
    assert subscriber.closed is True
    assert robot.is_connected is False


def test_wait_times_out_when_status_stream_is_not_fresh():
    robot = Mantis()
    robot._connected = True
    robot._system_status = {"motion_names": ["head"], "motion_states": [0]}

    with pytest.raises(TimeoutError, match="等待运动停止超时"):
        robot.wait(["head"], timeout=0.03)


def test_wait_rejects_non_positive_timeout():
    with pytest.raises(ValueError, match="timeout"):
        Mantis().wait(timeout=0)


def test_arm_is_moving_matches_status_names_without_joint_suffix():
    robot = Mantis()
    robot._system_status = {
        "motion_names": ["left_shoulder_pitch"],
        "motion_states": [1],
    }

    assert robot.left_arm.is_moving is True


def test_arm_is_moving_accepts_formal_standard_urdf_name():
    robot = Mantis()
    robot._system_status = {
        "motion_names": ["left_shoulder_pitch"],
        "motion_states": [1],
    }

    assert robot.is_moving(["A_left_Degree1_joint"]) is True


def test_chassis_defaults_match_documented_safe_limits():
    robot = _FakeRobot()
    chassis = Chassis(robot)
    robot.chassis = chassis

    assert chassis.DEFAULT_LINEAR_SPEED == 0.1
    assert chassis.MAX_LINEAR_SPEED == 0.5
    assert chassis.MAX_ANGULAR_SPEED == 1.0


def test_blocking_chassis_motion_stops_when_sleep_is_interrupted(monkeypatch):
    robot = _FakeRobot()
    chassis = Chassis(robot)
    robot.chassis = chassis

    def interrupt(_duration):
        raise KeyboardInterrupt

    monkeypatch.setattr("mantis.chassis.time.sleep", interrupt)

    with pytest.raises(KeyboardInterrupt):
        chassis.forward(0.1, speed=0.1)

    assert robot.commands[0] == (0.1, 0.0, 0.0)
    assert robot.commands[-1] == (0.0, 0.0, 0.0)


def test_new_nonblocking_chassis_command_cancels_old_stop_timer(monkeypatch):
    timers = []

    class FakeTimer:
        def __init__(self, duration, callback):
            self.duration = duration
            self.callback = callback
            self.daemon = False
            self.cancelled = False
            timers.append(self)

        def start(self):
            pass

        def cancel(self):
            self.cancelled = True

    robot = _FakeRobot()
    chassis = Chassis(robot)
    robot.chassis = chassis
    monkeypatch.setattr("mantis.chassis.threading.Timer", FakeTimer)

    chassis.forward(0.1, speed=0.1, block=False)
    chassis.turn_left(10, speed=0.5, block=False)

    assert len(timers) == 2
    assert timers[0].cancelled is True
    assert timers[1].cancelled is False


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_all_motion_modules_reject_non_finite_inputs(invalid):
    robot = Mantis()
    robot._connected = True

    operations = [
        lambda: robot.left_arm.set_joint(0, invalid, block=False),
        lambda: robot.left_arm.set_joints([invalid] * 7, block=False),
        lambda: robot.left_arm.ik(invalid, 0, 0, 0, 0, 0, block=False),
        lambda: robot.head.set_pitch(invalid, block=False),
        lambda: robot.head.set_roll(invalid, block=False),
        lambda: robot.left_gripper.set_position(invalid, block=False),
        lambda: robot.waist.set_height(invalid, block=False),
    ]

    for operation in operations:
        with pytest.raises(ValueError, match="有限数值"):
            operation()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_chassis_rejects_non_finite_inputs_before_publish(invalid):
    robot = _FakeRobot()
    chassis = Chassis(robot)
    robot.chassis = chassis

    with pytest.raises(ValueError, match="有限数值"):
        chassis.forward(invalid, block=False)
    with pytest.raises(ValueError, match="有限数值"):
        chassis.turn_left(invalid, block=False)

    assert robot.commands == []


@pytest.mark.parametrize("name", ["max_velocity", "max_acceleration", "max_jerk"])
@pytest.mark.parametrize("invalid", [0.0, -1.0, float("nan"), float("inf")])
def test_arm_motion_profile_requires_positive_finite_values(name, invalid):
    kwargs = {name: invalid}

    with pytest.raises(ValueError):
        Mantis().left_arm.set_joint(0, 0.0, block=False, **kwargs)
