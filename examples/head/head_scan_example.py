"""在头部限位内执行一组小幅度偏航扫描。"""

from __future__ import annotations

import argparse

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the Standard head yaw axis.")
    add_robot_arguments(parser)
    args = parser.parse_args()

    with connected_robot(args) as robot:
        limits = robot.head.limits
        print("head_limits=", limits)

        # 目标在 yaw -1.570 ~ 1.570、pitch -0.785 ~ 0.524 的安全范围内。
        # set_pose 使用绝对目标，block=True 保证每个观察点完成后再走下一个。
        for yaw in (-0.30, 0.30, 0.0):
            robot.head.set_pose(pitch=-0.05, yaw=yaw, block=True)
            print("target_pitch=%.3f target_yaw=%.3f" % (robot.head.pitch, robot.head.yaw))

        robot.head.center(block=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
