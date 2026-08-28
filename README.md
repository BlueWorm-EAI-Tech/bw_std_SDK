# Standard Robot Python SDK

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](./VERSION)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

面向 Standard 双臂机器人的 Python SDK。客户端通过 Zenoh 与机器人通信，不需要安装 ROS2；机器人端由 `bw_sdk_input` 接入已经跑通的 Standard/v3 控制、IK、平滑和串口链路。

当前版本只支持：

| 项目 | 固定配置 |
| --- | --- |
| 机器人型号 | `standard`，构造参数也接受缩写 `std` |
| 下位机协议 | `v3` |
| 手臂 | 左右各 7 轴，Standard `A_*_Degree1..7_joint` |
| IK | 机器人 ROS 侧解算，参考坐标系为 `C_Link` |
| 滑台 | 默认 `-100 mm`，硬件范围 `-500..0 mm` |
| 腰部弯腰 | 不支持 |

## 控制链路

```text
Python SDK
  -> Zenoh <SN>/sdk/*
  -> bw_sdk_input
  -> control_router / ArmCommandResolver / Smoother
  -> Standard v3 serial
  -> robot hardware
```

关节直控和 IK 都进入与 VR 遥操作相同的 resolver/smoother/串口出口。SDK 不在客户端执行 IK，也不携带机器人模型。

## 安装

客户端要求 Python 3.8 或更高版本：

```bash
cd /home/lanchong/standard-SDK
python3 -m pip install -e .
```

也可以只安装运行依赖：

```bash
python3 -m pip install eclipse-zenoh
```

## 启动机器人端

首次更新或机器人端代码有变化时构建主工作区：

```bash
cd /home/lanchong/standard_0828
./build.sh main
```

WiFi 启动：

```bash
./scripts/local/sdk_bridge.sh
# 等价于
./scripts/local/sdk_bridge.sh standard v3 wifi
```

有线模式：

```bash
./scripts/local/sdk_bridge.sh standard v3 wired
```

脚本会检查工作区来源和 CasADi 插件，配置网络，并显式启动：

```bash
ros2 launch bw_bringup system_composition.launch.py \
  mode:=sdk \
  robot_version:=standard \
  mantis_protocol_version:=v3 \
  ros_ip:=<ROBOT_IP>
```

`wired` 模式沿用 `start_real.sh` 的网络校验，需要在 `scripts/local/local.env` 中正确配置 `BW_WIRED_INTERFACE`、`BW_WIRED_STATIC_IP` 和 `BW_PICO_IP`。

## 快速开始

机器人运动前先确认周围无人、急停可用，并从小角度、低速度开始。

```python
from mantis import Mantis

with Mantis(ip="192.168.50.170") as robot:
    print(robot.robot_sn, robot.robot_ip, robot.robot_version)

    # 单关节命令只下发一个关节，不会覆盖另一只手臂。
    robot.left_arm.set_shoulder_pitch(-0.2)

    # 顺序为 Degree1..7：肩俯仰、肩翻滚、肩偏航、肘俯仰、腕翻滚、腕俯仰、腕偏航。
    robot.right_arm.set_joints([0.0, -0.2, 0.0, 0.3, 0.0, 0.0, 0.0])

    robot.left_gripper.open()
    robot.head.set_pose(pitch=0.0, yaw=0.2)
```

也可以按 SN 连接：

```python
from mantis import Mantis

robot = Mantis(sn="BW_XXXXXXX")
if not robot.connect(timeout=10):
    raise RuntimeError("Standard robot connection failed")
try:
    robot.left_arm.home()
finally:
    robot.disconnect()
```

不传 IP/SN 时使用 Zenoh 自动发现。多机器人现场建议显式传 `ip` 或 `sn`。

## 手臂关节

SDK 公共方法的 0..6 索引与 Standard Degree1..7 一一对应：

| 索引 | 公共语义 | Standard 正式关节 | 左臂范围 rad | 右臂范围 rad |
| --- | --- | --- | --- | --- |
| 0 | `shoulder_pitch` | `A_<side>_Degree1_joint` | `-2.069..1.022` | `-2.069..1.022` |
| 1 | `shoulder_roll` | `A_<side>_Degree2_joint` | `-0.142..2.077` | `-2.077..0.142` |
| 2 | `shoulder_yaw` | `A_<side>_Degree3_joint` | `-1.541..1.541` | `-1.541..1.541` |
| 3 | `elbow_pitch` | `A_<side>_Degree4_joint` | `-0.529..1.355` | `-0.529..1.355` |
| 4 | `wrist_roll` | `A_<side>_Degree5_joint` | `-1.540..1.540` | `-1.540..1.540` |
| 5 | `wrist_pitch` | `A_<side>_Degree6_joint` | `-0.756..0.756` | `-0.756..0.756` |
| 6 | `wrist_yaw` | `A_<side>_Degree7_joint` | `-1.017..1.018` | `-1.017..1.018` |

默认 `clamp=True` 会把目标限制在对应手臂限位内。常用接口：

```python
arm.set_joint(index, angle, block=True)
arm.set_joints([d1, d2, d3, d4, d5, d6, d7], block=True)
arm.set_shoulder_pitch(angle)
arm.set_shoulder_roll(angle)
arm.set_shoulder_yaw(angle)
arm.set_elbow_pitch(angle)
arm.set_wrist_roll(angle)
arm.set_wrist_pitch(angle)
arm.set_wrist_yaw(angle)
arm.home()
```

`set_joint()` 只发布该关节，`set_joints()` 只发布当前手臂 7 轴，`robot.home()` 才会一次发布双臂 14 轴零位。

## 机器人端 IK

绝对 IK 位姿以 `C_Link` 为参考坐标系，位置单位为米，RPY 单位为弧度：

```python
with Mantis(ip="192.168.50.170") as robot:
    # Standard 零关节角附近的左臂 Degree7 位姿。
    robot.left_arm.ik(
        0.329847758956320,
        0.178995684237027,
        -0.263747491045859,
        0.0, 0.0, 0.0,
        abs=True,
    )

    # 当前目标上的小增量：[dx, dy, dz, droll, dpitch, dyaw]。
    robot.left_arm.ik(0.01, 0.0, 0.01, 0.0, 0.0, 0.0, abs=False)
```

右臂零位参考为 `(0.329847758956320, -0.179005303496523, -0.263747491045859)`。绝对位姿应从该位置附近逐步验证，不要直接发送来源不明的大范围坐标。

可为单条手臂命令覆盖运动约束：

```python
robot.left_arm.ik(
    0.01, 0.0, 0.0, 0.0, 0.0, 0.0,
    abs=False,
    max_velocity=1.0,
    max_acceleration=3.0,
    max_jerk=20.0,
)
```

## 夹爪、头部、滑台和底盘

```python
with Mantis(ip="192.168.50.170") as robot:
    robot.left_gripper.set_position(0.5)  # 0=闭合，1=张开
    robot.right_gripper.open()

    # pitch -0.785..0.524 rad，yaw -1.570..1.570 rad
    robot.head.set_pose(pitch=-0.1, yaw=0.2)

    # 相对 Standard 默认 -100 mm 的高度，SDK 范围 -0.4..0.1 m
    robot.waist.set_speed(0.05)
    robot.waist.set_height(0.03)

    robot.chassis.forward(0.1, speed=0.1)
    robot.chassis.turn_left(15, speed=0.4)
```

Standard 没有前后弯腰轴。`set_bend()`、`bend_forward()`、`bend_backward()` 和 `set_bend_speed()` 会抛出 `NotImplementedError`。

## 阻塞与并行

手臂命令默认 `block=True`，SDK 根据相同 `command_id` 的机器人端完成状态返回。并行动作使用 `block=False`，最后显式等待：

```python
robot.left_arm.set_joints([0.0] * 7, block=False)
robot.right_arm.set_joints([0.0] * 7, block=False)
robot.wait()
```

## 示例

所有可运行示例位于 [examples](./examples/README.md)：

```bash
python -m examples.basic.connection_example --ip 192.168.50.170
python -m examples.arm.joint_control_example --ip 192.168.50.170 --side left
python -m examples.arm.ik_pose_example --ip 192.168.50.170 --side left --mode rel
python -m examples.waist.waist_height_example --ip 192.168.50.170
```

## 排查

| 现象 | 检查项 |
| --- | --- |
| 找不到机器人 | 机器人端 `sdk_bridge.sh` 是否运行；IP/SN 是否正确；客户端与机器人 Zenoh 网络是否互通 |
| 能发现但连接校验超时 | `<SN>/sdk/system_status` 是否持续发布；机器人端状态机是否启动 |
| 手臂命令无动作 | `mode:=sdk`、`robot_version:=standard`、`mantis_protocol_version:=v3` 是否生效；串口是否为 `/dev/ttyACM0` |
| IK 失败 | 目标是否使用 `C_Link` 坐标；先从上述零位参考附近用小增量验证 |
| 关节方向异常 | 机器人端是否使用 Standard `A_*_Degree*_joint`；不要再套用旧 2.0/3.0 方向表 |
| 滑台不动 | 输入是否在 `-0.4..0.1 m`；Standard 下位机物理范围是否已经到边界 |

## 开发验证

```bash
cd /home/lanchong/standard-SDK
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
python3 -m build
```

许可证见 [LICENSE](./LICENSE)。
