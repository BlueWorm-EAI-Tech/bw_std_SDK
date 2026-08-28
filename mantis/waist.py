"""Standard C 轴滑台控制。"""

from typing import TYPE_CHECKING

from ._validation import finite_float

if TYPE_CHECKING:
    from .mantis import Mantis


# Standard 默认位置 -100mm，硬件范围 -500mm ~ 0mm。
# SDK 暴露相对默认位置的米制位移，因此范围为 -0.4m ~ 0.1m。
WAIST_LIMITS = (-0.4, 0.1)


class Waist:
    """控制 Standard 滑台高度；Standard 不包含前后弯腰自由度。"""

    DEFAULT_SPEED = 0.1

    def __init__(self, robot: "Mantis"):
        self._robot = robot
        self._height = 0.0
        self._limits = WAIST_LIMITS
        self._speed = self.DEFAULT_SPEED
        self._bend_angle = 0.0

    @property
    def height(self) -> float:
        """相对默认位置的当前目标高度，单位为米。"""
        return self._height

    @property
    def limits(self) -> tuple:
        """相对默认位置的高度限位。"""
        return self._limits

    @property
    def bend_angle(self) -> float:
        """Standard 无弯腰轴，始终为 0。"""
        return 0.0

    def set_speed(self, speed: float):
        """设置滑台最大速度，单位为 m/s，范围 0.01-0.5。"""
        self._speed = max(0.01, min(0.5, abs(finite_float(speed, "speed"))))

    @staticmethod
    def _ensure_bend_supported() -> None:
        raise NotImplementedError("Standard 机器人不支持腰部前后弯腰控制")

    def set_bend_speed(self, speed: float):
        """Standard 不支持前后弯腰。"""
        self._ensure_bend_supported()

    def set_bend(self, angle: float, clamp: bool = True, block: bool = True):
        """Standard 不支持前后弯腰。"""
        self._ensure_bend_supported()

    def bend_forward(self, angle: float = 0.3, block: bool = True):
        """Standard 不支持前倾弯腰。"""
        self._ensure_bend_supported()

    def bend_backward(self, angle: float = 0.2, block: bool = True):
        """Standard 不支持后仰。"""
        self._ensure_bend_supported()

    def _clamp(self, value: float) -> float:
        value = finite_float(value, "height")
        lower, upper = self._limits
        return max(lower, min(upper, value))

    def _execute_motion(self, block: bool):
        if block:
            self.wait()

    def wait(self):
        self._robot.wait(["waist"])

    @property
    def is_moving(self) -> bool:
        return self._robot.is_moving(["waist"])

    def set_height(self, height: float, clamp: bool = True, block: bool = True):
        """设置相对默认位置的目标高度，单位为米。"""
        self._height = self._clamp(height) if clamp else finite_float(height, "height")
        self._robot._publish_waist()
        self._execute_motion(block)

    def up(self, delta: float = 0.05, block: bool = True):
        self.move(abs(delta), block=block)

    def down(self, delta: float = 0.05, block: bool = True):
        self.move(-abs(delta), block=block)

    def home(self, block: bool = True):
        self.set_height(0.0, block=block)

    def move(self, delta: float, block: bool = True):
        self.set_height(self._height + finite_float(delta, "delta"), block=block)

    def __repr__(self) -> str:
        return f"Waist(height={self._height:.3f}m)"
