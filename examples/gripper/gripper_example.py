from __future__ import annotations

import argparse
import math
import sys
import time

from examples.common import add_common_motion_arguments, add_robot_arguments, connected_robot


def main() -> int:
    parser = argparse.ArgumentParser(description="Set only the selected gripper; 0 closed, 1 open.")
    add_robot_arguments(parser)
    add_common_motion_arguments(parser)
    parser.add_argument('--side', choices=('left', 'right', 'both'), default='left')
    parser.add_argument('--position', type=float, default=0.5)
    parser.add_argument('--finish-position', type=float, default=1.0,
                        help='Final opening (default 1); this does not disable motor torque.')
    parser.add_argument('--hold', type=float, default=0.5, help='Seconds before the final target.')
    args = parser.parse_args()
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in (args.position, args.finish_position)):
        parser.error('positions must be finite and within 0..1')
    if not math.isfinite(args.hold) or not 0 <= args.hold <= 10:
        parser.error('hold must be within 0..10 seconds')
    with connected_robot(args) as robot:
        grippers = [getattr(robot, side + '_gripper') for side in ('left', 'right')
                    if args.side in (side, 'both')]
        try:
            for gripper in grippers:
                gripper.set_position(args.position, block=not args.non_blocking)
            if args.non_blocking:
                for gripper in grippers:
                    gripper.wait()
            time.sleep(args.hold)
        finally:
            # Also attempt the final opening after a wait error or Ctrl+C.
            # Connection/source failure can still prevent this position command.
            pending_error = sys.exc_info()[0] is not None
            errors = []
            for gripper in grippers:
                try:
                    gripper.set_position(args.finish_position, block=True)
                except Exception as error:
                    errors.append(error)
                    print(f'{gripper.side}: final opening failed: {error}', file=sys.stderr)
            if errors and not pending_error:
                raise errors[0]
        print(f"夹爪完成：{args.side} {args.position} → {args.finish_position}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
