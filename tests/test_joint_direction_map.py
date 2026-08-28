import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONSTANTS_FILE = REPO_ROOT / "mantis" / "constants.py"


def _load_constants_module():
    spec = importlib.util.spec_from_file_location("mantis_constants", CONSTANTS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sdk_constants_no_longer_export_joint_direction_maps():
    constants = _load_constants_module()

    assert not hasattr(constants, "JOINT_DIRECTION_MAP")
    assert not hasattr(constants, "JOINT_DIRECTION_MAP_2_0")
    assert not hasattr(constants, "JOINT_DIRECTION_MAP_3_0")
    assert not hasattr(constants, "JOINT_DIRECTION_MAPS")
