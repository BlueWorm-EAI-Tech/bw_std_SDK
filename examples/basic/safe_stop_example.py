"""演示底盘非阻塞运动和异常安全清理。

这个示例只移动底盘，不会发送手臂、头部或夹爪目标。按 Ctrl-C 时，
``finally`` 会立即发布零速度；这不是硬件急停，现场仍必须准备急停按钮。
"""

from __future__ import annotations

import argparse
import time

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Demonstrate safe chassis stop handling.")
    add_robot_arguments(parser)
    parser.add_argument("--duration", type=float, default=2.0)
    args = parser.parse_args()

    with connected_robot(args) as robot:
        try:
            robot.chassis.forward(0.10, speed=0.05, block=False)
            print("底盘已开始前进；按 Ctrl-C 可提前停止")
            time.sleep(max(args.duration, 0.1))
        except KeyboardInterrupt:
            print("收到 Ctrl-C，正在停止底盘")
        finally:
            robot.chassis.stop()
            print("底盘已发送零速度")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
