"""持续打印 Standard system_status 的关键变化。"""

from __future__ import annotations

import argparse
import threading
import time

from examples.common import add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Monitor system_status without sending motion commands."
    )
    add_robot_arguments(parser, require_target=False)
    parser.add_argument("--duration", type=float, default=10.0)
    args = parser.parse_args()

    lock = threading.Lock()
    last_snapshot = None

    def on_status(data: dict) -> None:
        # 回调运行在 Zenoh 接收线程；只在锁内复制需要打印的字段，避免
        # 阻塞网络线程或直接持有 SDK 内部状态对象。
        nonlocal last_snapshot
        snapshot = (
            data.get("system_state"),
            data.get("control_source"),
            tuple(
                (name, state)
                for name, state in zip(
                    data.get("motion_names", []), data.get("motion_states", [])
                )
                if state == 1
            ),
        )
        with lock:
            if snapshot == last_snapshot:
                return
            last_snapshot = snapshot
        print(
            "system_state=%r control_source=%r moving=%s"
            % (snapshot[0], snapshot[1], list(snapshot[2]))
        )

    with connected_robot(args, require_target=False) as robot:
        robot.subscribe_status(on_status)
        end_time = time.monotonic() + max(args.duration, 0.1)
        while time.monotonic() < end_time:
            time.sleep(0.1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
