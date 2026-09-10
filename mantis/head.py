"""Standard 机器人头部控制。

头部提供三个自由度：俯仰 ``pitch``、偏航 ``yaw`` 和滚转 ``roll``。
角度单位为弧度，``set_pose`` 的缺省 ``clamp=True`` 会把目标限制到
Standard 真机限位内。
头部命令没有手臂那样的独立 command id，阻塞等待依赖机器人状态话题；
因此生产程序应保留合理的等待超时和断开清理逻辑。

Example:
    .. code-block:: python
    
        from mantis import Mantis
        
        with Mantis(ip="192.168.1.100") as robot:
            # 阻塞模式（默认）
            robot.head.look_left()
            
            # 非阻塞模式（与手臂并行）
            robot.head.look_left(block=False)
            robot.left_arm.set_shoulder_pitch(-0.5, block=False)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mantis import Mantis

from .constants import HEAD_LIMITS
from ._validation import finite_float


# 动作定义：(方法名, 参数名, 符号, 默认值, 说明)。
# look_left/right 和 look_up/down 都把对应轴设置为绝对目标值，
# 不是相对增量或速度命令；传入负角度时仍按动作名称决定方向。
_LOOK_ACTIONS = [
    ("look_left",  "yaw",   1,  0.5, "向左看"),
    ("look_right", "yaw",  -1,  0.5, "向右看"),
    ("look_up",    "pitch", -1, 0.3, "向上看"),
    ("look_down",  "pitch", 1,  0.3, "向下看"),
]


def _make_look_action(attr: str, sign: int, default: float, doc: str):
    """工厂函数：生成 look_xxx 方法。"""
    def action(self, angle: float = default, block: bool = True):
        """执行头部动作。
        
        Args:
            angle: 角度大小（弧度），默认使用预设值
            block: 是否阻塞等待完成，默认 True
        """
        new_value = sign * abs(finite_float(angle, "angle"))
        setattr(self, f"_{attr}", new_value)
        self._apply_limits()
        
        self._robot._publish_head()
        self._execute_motion(block)
        
    action.__doc__ = f"""{doc}。
    
    Args:
        angle: 角度大小（弧度），默认 {default}
        block: 是否阻塞等待完成，默认 True
    """
    return action


class Head:
    """头部控制器。
    
    头部有 3 个自由度：
    
    ========  ==============  ==================
    轴        中文名          范围 (rad)
    ========  ==============  ==================
    pitch     俯仰            -0.785 ~ 0.524
    yaw       偏航            -1.570 ~ 1.570
    roll      滚转            -0.349 ~ 0.349
    ========  ==============  ==================
    
    支持阻塞/非阻塞模式：
        - block=True（默认）：等待运动完成后返回
        - block=False：立即返回，运动在后台执行
    
    Attributes:
        pitch: 当前俯仰角（弧度）
        yaw: 当前偏航角（弧度）
        roll: 当前滚转角（弧度）
        is_moving: 是否正在运动中
    
    Example:
        .. code-block:: python
        
            # 阻塞模式
            robot.head.look_left(0.5)
            
            # 非阻塞模式
            robot.head.look_left(0.5, block=False)
            robot.head.wait()  # 等待完成
    """
    
    #: 默认头部速度 (rad/s)
    DEFAULT_SPEED = 1.0
    
    def __init__(self, robot: "Mantis"):
        """初始化头部控制器。"""
        self._robot = robot
        self._pitch = 0.0
        self._yaw = 0.0
        self._roll = 0.0
        self._limits = HEAD_LIMITS
        self._speed = self.DEFAULT_SPEED
    
    @property
    def pitch(self) -> float:
        """当前俯仰角（弧度）。"""
        return self._pitch
    
    @property
    def yaw(self) -> float:
        """当前偏航角（弧度）。"""
        return self._yaw

    @property
    def roll(self) -> float:
        """当前滚转角（弧度）。"""
        return self._roll

    @property
    def limits(self) -> dict:
        """限位字典。"""
        return self._limits.copy()
    
    def set_speed(self, speed: float):
        """设置头部运动速度。
        
        Args:
            speed: 速度 (rad/s)，有效范围 0.1 ~ 3.0；超出范围时自动截断。

        Note:
            当前 Standard v3 桥接协议只把头部目标角度发送给机器人端，
            速度设置用于保留统一 API 语义，具体轨迹由机器人端执行。
        """
        self._speed = max(0.1, min(3.0, abs(finite_float(speed, "speed"))))
    
    def _clamp(self, attr: str, value: float) -> float:
        """限制值在限位范围内。"""
        value = finite_float(value, attr)
        lower, upper = self._limits[attr]
        return max(lower, min(upper, value))
    
    def _apply_limits(self):
        """应用限位。"""
        self._pitch = self._clamp("pitch", self._pitch)
        self._yaw = self._clamp("yaw", self._yaw)
        self._roll = self._clamp("roll", self._roll)
    
    def _execute_motion(self, block: bool):
        """执行运动。"""
        if block:
            self.wait()
    
    def wait(self):
        """等待当前运动完成。"""
        self._robot.wait(['head'])
    
    @property
    def is_moving(self) -> bool:
        """是否正在运动中。"""
        return self._robot.is_moving(['head'])
    
    def set_pose(
        self,
        pitch: float = None,
        yaw: float = None,
        clamp: bool = True,
        block: bool = True,
        *,
        roll: float = None,
    ):
        """设置头部姿态。
        
        Args:
            pitch: 俯仰角（弧度），闭区间 -0.785 ~ 0.524；``None`` 表示保持当前值。
            yaw: 偏航角（弧度），闭区间 -1.570 ~ 1.570；``None`` 表示保持当前值。
            roll: 滚转角（弧度），闭区间 -0.349 ~ 0.349；``None`` 表示保持当前值。
            clamp: 是否自动限制在限位范围内，默认 True。设为 False 时，
                只校验有限数值，不在客户端截断，最终是否接受由机器人端决定。
            block: 是否阻塞等待完成，默认 True。

        Example:
            ``robot.head.set_pose(pitch=-0.1, yaw=0.25, roll=0.05)`` 发送完整
            头部目标；只传一个轴时，其余轴保持当前目标。
        """
        
        if pitch is not None:
            self._pitch = self._clamp("pitch", pitch) if clamp else finite_float(pitch, "pitch")
        if yaw is not None:
            self._yaw = self._clamp("yaw", yaw) if clamp else finite_float(yaw, "yaw")
        if roll is not None:
            self._roll = self._clamp("roll", roll) if clamp else finite_float(roll, "roll")
        
        self._robot._publish_head()
        self._execute_motion(block)
    
    def set_pitch(self, angle: float, clamp: bool = True, block: bool = True):
        """设置俯仰角。
        
        Args:
            angle: 目标角度（弧度）
            clamp: 是否限位
            block: 是否阻塞
        """
        self.set_pose(pitch=angle, clamp=clamp, block=block)
    
    def set_yaw(self, angle: float, clamp: bool = True, block: bool = True):
        """设置偏航角。
        
        Args:
            angle: 目标角度（弧度）
            clamp: 是否限位
            block: 是否阻塞
        """
        self.set_pose(yaw=angle, clamp=clamp, block=block)

    def set_roll(self, angle: float, clamp: bool = True, block: bool = True):
        """设置滚转角。

        Args:
            angle: 目标角度（弧度），闭区间 -0.349 ~ 0.349。
            clamp: 是否自动限制到头部滚转限位，默认 True。
            block: 是否阻塞等待完成，默认 True。
        """
        self.set_pose(roll=angle, clamp=clamp, block=block)
    
    def center(self, block: bool = True):
        """回中（俯仰、偏航和滚转都归零）。
        
        Args:
            block: 是否阻塞等待完成，默认 True
        """
        self.set_pose(pitch=0.0, yaw=0.0, roll=0.0, block=block)
    
    def __repr__(self) -> str:
        """返回头部的字符串表示。"""
        status = "运动中" if self.is_moving else "停止"
        return (
            f"Head({status}, pitch={self._pitch:.2f}, "
            f"yaw={self._yaw:.2f}, roll={self._roll:.2f})"
        )


# 动态生成 look_xxx 方法
for name, attr, sign, default, doc in _LOOK_ACTIONS:
    setattr(Head, name, _make_look_action(attr, sign, default, doc))
