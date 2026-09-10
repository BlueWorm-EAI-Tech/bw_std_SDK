"""让底盘走一个很小的方形路径。

每一段都使用阻塞模式，确保上一段已经自动发送零速度后才开始下一段。
``finally`` 中仍然显式调用 ``stop``，便于 Ctrl-C 或其他异常时清理底盘。
"""

from __future__ import annotations

import argparse

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Drive a short safe chassis square.")
    add_robot_arguments(parser)
    parser.add_argument("--side", type=float, default=0.05, help="Side length in meters.")
    args = parser.parse_args()

    if not 0.01 <= args.side <= 0.20:
        raise SystemExit("--side must be within 0.01 ~ 0.20 m")

    with connected_robot(args) as robot:
        chassis = robot.chassis
        chassis.set_default_speed(linear=0.05, angular=0.25)
        try:
            for index in range(4):
                chassis.forward(args.side, block=True)
                chassis.turn_left(90, block=True)
                print("completed_side=", index + 1)
        finally:
            # stop() 只影响底盘；上下文管理器随后还会断开 Zenoh。
            chassis.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
