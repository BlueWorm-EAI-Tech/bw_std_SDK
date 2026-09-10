"""在头部限位内执行一组小幅度三轴姿态扫描。"""

from __future__ import annotations

import argparse

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the Standard head pitch/yaw/roll axes.")
    add_robot_arguments(parser)
    args = parser.parse_args()

    with connected_robot(args) as robot:
        limits = robot.head.limits
        print("head_limits=", limits)

        # 目标在 pitch -0.785 ~ 0.524、yaw -1.570 ~ 1.570、
        # roll -0.349 ~ 0.349 的安全范围内。
        # set_pose 使用绝对目标，block=True 保证每个观察点完成后再走下一个。
        for yaw, roll in ((-0.30, -0.05), (0.30, 0.05), (0.0, 0.0)):
            robot.head.set_pose(pitch=-0.05, yaw=yaw, roll=roll, block=True)
            print(
                "target_pitch=%.3f target_yaw=%.3f target_roll=%.3f"
                % (robot.head.pitch, robot.head.yaw, robot.head.roll)
            )

        robot.head.center(block=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
