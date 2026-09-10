"""运行运动程序前的只读检查。

这个示例不会发送任何运动命令，适合在真实机器人上电后首先执行。它会
确认身份已经解析、状态话题有数据，并提示当前是否已经有部件在运动。
"""

from __future__ import annotations

import argparse
import json

from examples.common import add_robot_arguments, connected_robot, print_robot_identity


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a read-only preflight check before robot motion."
    )
    add_robot_arguments(parser, require_target=False)
    args = parser.parse_args()

    # verify=True 是默认值：连接时会等待匹配 SN 的 system_status。
    with connected_robot(args, require_target=False) as robot:
        print_robot_identity(robot)

        status = robot.system_status or {}
        motion_names = status.get("motion_names", [])
        motion_states = status.get("motion_states", [])
        moving = [
            name
            for name, state in zip(motion_names, motion_states)
            if state == 1
        ]

        print("supports_ik=", robot.supports_ik)
        print("status_fields=", sorted(status))
        print("moving_components=", moving)
        print("is_any_moving=", robot.is_any_moving)
        print("system_status=")
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))

        if not status:
            raise RuntimeError("未收到 system_status，不能开始运动")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
