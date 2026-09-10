"""双臂同步发送一组小幅度关节目标。

示例重点是 ``block=False``、机器人端 command id 和 ``robot.wait()`` 的
配合。目标角度刻意保持在零位附近，首次运行仍需确认现场安全。
"""

from __future__ import annotations

import argparse

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Move both Standard arms together.")
    add_robot_arguments(parser)
    args = parser.parse_args()

    left_pose = [0.12, 0.08, 0.0, 0.20, 0.0, 0.0, 0.0]
    right_pose = [0.12, -0.08, 0.0, 0.20, 0.0, 0.0, 0.0]

    with connected_robot(args) as robot:
        # 先回到已知起点，避免示例依赖上一次程序留下的目标。
        robot.home(block=True)

        # 两条命令立即返回；机器人端分别报告完成，robot.wait() 会等待两条命令。
        robot.left_arm.set_joints(
            left_pose,
            block=False,
            max_velocity=0.8,
            max_acceleration=2.0,
            max_jerk=10.0,
        )
        robot.right_arm.set_joints(
            right_pose,
            block=False,
            max_velocity=0.8,
            max_acceleration=2.0,
            max_jerk=10.0,
        )
        robot.wait(timeout=10.0)

        print("left_positions=", robot.left_arm.positions)
        print("right_positions=", robot.right_arm.positions)
        print("is_any_moving=", robot.is_any_moving)

        # 示例结束时恢复零位，方便下一次运行。
        robot.home(block=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
