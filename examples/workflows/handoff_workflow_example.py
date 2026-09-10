"""一个阶段化的双臂交接工作流示例。

示例展示如何把动作拆成“准备、交接、收尾”三个阶段，并在每个阶段明确
等待点。这里使用零位附近的关节目标，不包含依赖具体工装的 IK 坐标。
"""

from __future__ import annotations

import argparse

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small two-arm handoff workflow.")
    add_robot_arguments(parser)
    args = parser.parse_args()

    with connected_robot(args) as robot:
        # 阶段 1：把机器人放到已知起点，打开两侧夹爪。
        robot.home(block=True)
        robot.left_gripper.open(block=False)
        robot.right_gripper.open(block=False)
        robot.wait([robot.left_gripper.joint_name, robot.right_gripper.joint_name])

        # 阶段 2：两臂同时移动到交接高度。左右肩翻滚符号相反，保持镜像姿态。
        robot.left_arm.set_joints(
            [0.10, 0.08, 0.0, 0.20, 0.0, 0.0, 0.0], block=False
        )
        robot.right_arm.set_joints(
            [0.10, -0.08, 0.0, 0.20, 0.0, 0.0, 0.0], block=False
        )
        robot.head.set_pose(pitch=-0.05, yaw=0.0, block=False)
        robot.wait(timeout=10.0)

        # 阶段 3：右侧夹爪先闭合，再让左侧夹爪释放，完成一次简单交接。
        robot.right_gripper.set_position(0.35, block=True)
        robot.left_gripper.open(block=True)

        # 收尾：所有目标回到可重复的安全起点。
        robot.home(block=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
