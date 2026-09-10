# Standard Robot Python SDK

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](./VERSION)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

面向 Standard 双臂机器人的 Python SDK。客户端通过 Zenoh 与机器人端
`bw_sdk_input` 通信，不需要安装 ROS2。当前 SDK、机器人端桥接程序和
Standard v3 下位机协议需要配套使用。

## 1. 支持范围

“当前版本只支持”是指以下能力已经在 Standard 配置中定义并经过 SDK
测试；未列出的能力不要按其他机器人 SDK 的接口习惯自行推断。

| 模块 | 当前支持 | 单位和范围 |
| --- | --- | --- |
| 机器人配置 | `standard`，也接受 `std` | 下位机协议固定为 `v3` |
| 左臂、右臂 | 每侧 7 个关节；单关节、整臂关节目标、机器人端 IK | 角度 rad；限位见[手臂](#6-手臂) |
| 头部 | 俯仰 `pitch`、偏航 `yaw`、滚转 `roll`，共 3 个自由度 | `pitch: -0.785 ~ 0.524 rad`；`yaw: -1.570 ~ 1.570 rad`；`roll: -0.349 ~ 0.349 rad` |
| 夹爪 | 左右夹爪开合和归一化位置 | `0.0 ~ 1.0`，0.0 闭合、1.0 张开 |
| 滑台 | 升降、相对默认高度移动和回零 | SDK 位移 `-0.4 ~ 0.1 m`；硬件位置 `-500 ~ 0 mm` |
| 全向底盘 | 前后、左右平移、原地旋转 | 距离 m，角度 degree，速度 rad/s 或 m/s |
| 连接与发现 | 按 IP、SN 连接；局域网自动发现；SN 话题隔离 | Zenoh 默认端口 `7447` |
| 状态 | 系统状态订阅、运动状态、手臂命令完成状态 | JSON 字典；见[状态与错误处理](#9-状态与错误处理) |

## 2. 统一约定

### 2.1 区间和单位

- 文档中的 `下限 ~ 上限` 表示闭区间，两端值都可能被接受；不再使用容易误解的 `..`。
- 关节角、头部角度和 IK 姿态使用弧度 `rad`。
- IK 位置、滑台高度和底盘平移使用米 `m`。
- 底盘 `turn_left()` / `turn_right()` 的输入角度使用 degree；底层角速度使用 `rad/s`。
- 夹爪位置是无量纲归一化值，不是米或 degree。

### 2.2 限位、阻塞和停止

- 关节、头部和滑台默认 `clamp=True`，超出范围会截断到限位；设为 `False` 时只校验是否为有限数值，最终由机器人端决定是否接受。
- `block=True` 是默认值：命令发送后等待完成再返回。`block=False` 立即返回，随后用模块的 `wait()` 或 `robot.wait()` 等待。
- 手臂命令带有 `command_id`，阻塞等待会等待对应命令的完成或失败状态。
- `robot.stop()` 和 `robot.chassis.stop()` 只发送底盘零速度，不是硬件急停，也不会撤销手臂、头部或夹爪目标。危险情况必须使用机器人硬件急停。
- 运动前确认急停可用、周围无人和障碍物清空，并从小幅度、低速度开始。

## 3. 控制链路

SDK 运行模式和真机 VR 遥操作共用机器人端的控制路由、运动学解算、运动
平滑和串口出口。`start_real.sh` 启动真机 VR 输入，`sdk_bridge.sh` 启动
SDK 输入；两者在路由后汇聚到同一条执行链路：

```text
Python SDK
  -> <SN>/sdk/* (Zenoh)
  -> bw_sdk_input
  -> <SN>/input/sdk/*
  -> control_router_node
  -> <SN>/ctrl/selected_robot_command
  -> robot_command_dispatcher_node
  -> 手臂: ctrl/selected_arm_command
  -> ArmCommandResolverNode / IK
  -> ctrl/selected_joint_angle_solution
  -> SmootherNode
  -> Teleop/joint_angle_solution/smooth
  -> bw_serial / mantis_comm_node
  -> Standard v3 serial
  -> robot hardware
```

头部、夹爪、底盘和滑台由 dispatcher 分发到对应的 `Teleop/*` 执行入口，
不经过手臂 IK 和 smoother。真机 VR 遥操作由
`start_real.sh standard v3 wifi` 启动，数据链路为：

```text
PICO / Unity VR
  -> bw_vr_bridge
  -> bw_vr_input
  -> input/vr/*
  -> teleop_input_selector_node
  -> Teleop/*/raw
  -> bw_teleop / GripperModeConverter
  -> target_left_pose、target_right_pose 和其他模块输入
  -> control_router_node
  -> <SN>/ctrl/selected_robot_command
  -> robot_command_dispatcher_node
  -> 与 SDK 相同的 resolver / smoother / bw_serial 出口
```

SDK 只负责发送按 SN 隔离的 JSON 目标，不在客户端执行 IK 或运动平滑；
客户端不需要 ROS2、URDF、Pinocchio 或 CasADi。头部 `head_pose` 使用
`head_pitch_joint`、`head_yaw_joint`、`head_roll_joint` 三个关节名，
与真机 VR 链路保持一致。手臂命令若携带 `command_id`，状态会沿同一
路由返回 SDK，客户端可通过 `wait()` 等待 `ROUTED`、`RESOLVED` 和
`COMPLETED` 状态。

## 4. 安装和启动

客户端要求 Python 3.8 或更高版本：

```bash
cd standard-SDK
python3 -m pip install -e .
```

只安装运行依赖时：

```bash
python3 -m pip install eclipse-zenoh
```

首次更新机器人端代码或工作区后，先构建：

```bash
cd <robot_workspace>
./build.sh main
```

WiFi 模式：

```bash
./scripts/local/sdk_bridge.sh standard v3 wifi
```

有线模式：

```bash
./scripts/local/sdk_bridge.sh standard v3 wired
```

脚本最终应启动：

```bash
ros2 launch bw_bringup system_composition.launch.py \
  mode:=sdk \
  robot_version:=standard \
  mantis_protocol_version:=v3 \
  ros_ip:=<ROBOT_IP>
```

有线模式还需要在 `scripts/local/local.env` 中配置
`BW_WIRED_INTERFACE`、`BW_WIRED_STATIC_IP` 和 `BW_PICO_IP`。如果客户端
与机器人不在同一 Zenoh 网络，SDK 无法发现身份或状态。

## 5. 快速开始

推荐使用上下文管理器。退出代码块时会断开 Zenoh 会话并发送底盘停止命令。

```python
from mantis import Mantis

with Mantis(ip="192.168.50.170") as robot:
    print(robot.robot_sn, robot.robot_ip, robot.robot_version)

    # 单关节命令只更新左臂的 Degree1，不会覆盖右臂目标。
    robot.left_arm.set_shoulder_pitch(-0.2)

    # 顺序固定为 Degree1 ~ Degree7。
    robot.right_arm.set_joints([0.0, -0.2, 0.0, 0.3, 0.0, 0.0, 0.0])

    robot.left_gripper.open()
    robot.head.set_pose(pitch=0.0, yaw=0.2, roll=0.0)
    robot.chassis.forward(0.05, speed=0.05)
```

按 SN 连接：

```python
from mantis import Mantis

robot = Mantis(sn="BW_XXXXXXX")
if not robot.connect(timeout=10):
    raise ConnectionError("Standard robot connection failed")
try:
    print(robot.system_status)
    robot.left_arm.home()
finally:
    robot.disconnect()
```

不传 IP 或 SN 时，`connect()` 会通过全局 `sn` 话题自动发现。多机器人
现场建议显式传入 `ip` 或 `sn`，并在运行前核对打印出的 `robot_sn`。

## 6. 手臂

每侧手臂都是 7 轴，公共索引 0 ~ 6 与 Standard `Degree1 ~ Degree7`
一一对应。下表为 SDK 限位，单位为 rad，区间两端均包含。

| 索引 | 公共名称 | Standard 正式关节 | 左臂 | 右臂 |
| ---: | --- | --- | ---: | ---: |
| 0 | `shoulder_pitch` | `A_<side>_Degree1_joint` | `-2.069 ~ 1.022` | `-2.069 ~ 1.022` |
| 1 | `shoulder_roll` | `A_<side>_Degree2_joint` | `-0.142 ~ 2.077` | `-2.077 ~ 0.142` |
| 2 | `shoulder_yaw` | `A_<side>_Degree3_joint` | `-1.541 ~ 1.541` | `-1.541 ~ 1.541` |
| 3 | `elbow_pitch` | `A_<side>_Degree4_joint` | `-0.529 ~ 1.355` | `-0.529 ~ 1.355` |
| 4 | `wrist_roll` | `A_<side>_Degree5_joint` | `-1.540 ~ 1.540` | `-1.540 ~ 1.540` |
| 5 | `wrist_pitch` | `A_<side>_Degree6_joint` | `-0.756 ~ 0.756` | `-0.756 ~ 0.756` |
| 6 | `wrist_yaw` | `A_<side>_Degree7_joint` | `-1.017 ~ 1.018` | `-1.017 ~ 1.018` |

常用接口：

```python
arm = robot.left_arm
arm.set_speed(0.8)  # 客户端记录的默认速度，单位 rad/s，接受范围 0.1 ~ 3.0
arm.set_joint(0, -0.2)  # 单个关节，索引 0 ~ 6
arm.set_shoulder_pitch(-0.2)
arm.set_joints([0.0, 0.1, 0.0, 0.2, 0.0, 0.0, 0.0])
arm.home()

print(arm.positions)  # 当前目标角度的副本
print(arm.limits)     # 当前手臂的 7 组限位
```

`set_joint()` 只发布一个关节，`set_joints()` 只发布当前手臂的 7 轴。
只有 `robot.home()` 才会一次发布双臂 14 轴、头部回中、夹爪闭合和滑台
回到默认高度。

### 6.1 机器人端 IK

绝对 IK 姿态以机器人端 `C_Link` 为参考坐标系，位置单位为 m，RPY 单位
为 rad。客户端只发送目标，不执行 IK。

```python
with Mantis(ip="192.168.50.170") as robot:
    # Standard 零关节角附近的左臂 Degree7 参考姿态。
    robot.left_arm.ik(
        0.329847758956320,
        0.178995684237027,
        -0.263747491045859,
        0.0, 0.0, 0.0,
        abs=True,
    )

    # 在当前目标上增加 [dx, dy, dz, droll, dpitch, dyaw]。
    robot.left_arm.ik(0.01, 0.0, 0.01, 0.0, 0.0, 0.0, abs=False)
```

右臂零位参考为
`(0.329847758956320, -0.179005303496523, -0.263747491045859)`。
绝对姿态必须从参考点附近逐步验证，不能直接发送来源不明的大范围坐标。
相对 IK 还可以附带机器人端运动约束：

```python
robot.left_arm.ik(
    0.01, 0.0, 0.0, 0.0, 0.0, 0.0,
    abs=False,
    max_velocity=1.0,
    max_acceleration=3.0,
    max_jerk=20.0,
)
```

## 7. 头部

头部有三个轴：

| 参数 | 含义 | 闭区间 | 正方向 |
| --- | --- | --- | --- |
| `pitch` | 俯仰 | `-0.785 ~ 0.524 rad` | `set_pitch()` 的正值按机器人端定义 |
| `yaw` | 偏航 | `-1.570 ~ 1.570 rad` | 正值向左 |
| `roll` | 滚转 | `-0.349 ~ 0.349 rad` | 正方向按机器人端定义 |

`set_pose()` 可以只更新一个轴，传 `None` 的轴保持当前目标。`look_left()`、
`look_right()`、`look_up()` 和 `look_down()` 是偏航/俯仰便捷方法；滚转使用
`set_roll()` 或 `set_pose(roll=...)`。

```python
head = robot.head
print(head.limits)
head.set_pose(pitch=-0.1, yaw=0.25, roll=0.05)
head.set_roll(-0.05, block=False)
head.look_left(0.2, block=False)
head.wait()
head.center()
```

头部命令支持 `block=True` 和 `block=False`。头部状态基于
`system_status` 判断，生产程序应对 `wait()` 设置合理超时。

## 8. 底盘、夹爪和滑台

### 8.1 全向底盘

底盘使用有限时长的“距离/角度 + 速度”接口。每条命令结束后 SDK 会发
送零速度；新的非阻塞命令会取消旧的停止定时器。

| 项目 | 约定 |
| --- | --- |
| `x` | 前后距离，正值前进、负值后退，单位 m |
| `y` | 左右距离，正值左移、负值右移，单位 m |
| `angle` | 原地旋转，正值左转、负值右转，单位 degree |
| 线速度 | 默认 `0.1 m/s`，接受范围 `0.01 ~ 0.5 m/s` |
| 角速度 | 默认 `0.3 rad/s`，接受范围 `0.1 ~ 1.0 rad/s` |
| 摩擦补偿 | 默认 `1.0`，实际接受范围 `0.5 ~ 5.0` |

```python
chassis = robot.chassis
chassis.set_default_speed(linear=0.1, angular=0.3)
chassis.set_friction(linear=1.2, angular=1.1)

chassis.forward(0.10)
chassis.strafe_left(0.05)
chassis.turn_right(15, speed=0.3)

# move() 按“先平移、后旋转”的顺序执行，不是同时合成速度。
chassis.move(x=0.10, y=0.05, angle=10, linear_speed=0.08, angular_speed=0.3)

# 非阻塞后显式停止等待。
chassis.forward(0.10, speed=0.05, block=False)
chassis.wait()
chassis.stop()
```

`forward()`、`backward()`、`strafe_left()`、`strafe_right()`、
`turn_left()` 和 `turn_right()` 的运动量参数必须是正数，方向由方法名
决定；需要有符号运动量时使用 `move()`。

### 8.2 夹爪

```python
robot.left_gripper.open()
robot.right_gripper.set_position(0.35, block=False)
robot.right_gripper.wait()
robot.left_gripper.close()
```

`open()`、`close()`、`half_open()` 分别等价于位置 1.0、0.0、0.5。
`set_position()` 会把目标限制在 `0.0 ~ 1.0`。

### 8.3 滑台

滑台的 `height` 属性是相对默认位置（硬件 `-100 mm`）的位移，单位 m。
硬件 `-500 ~ 0 mm` 对应 SDK `-0.4 ~ 0.1 m`。

```python
robot.waist.set_speed(0.05)
robot.waist.up(0.03)
robot.waist.down(0.03)
robot.waist.set_height(0.0)
```

## 9. 连接、状态与错误处理

连接时 SDK 先从全局 `sn` 话题解析 `(sn, ip)`，再把发布和订阅话题限定为
`<SN>/sdk/*`，最后默认等待 `<SN>/sdk/system_status` 做第二次校验。连接
失败返回 `False`，资源会自动关闭；上下文管理器连接失败则抛出
`ConnectionError`。

```python
def on_status(data: dict) -> None:
    print("system_state:", data.get("system_state"))
    print("control_source:", data.get("control_source"))
    print("motion:", list(zip(data.get("motion_names", []), data.get("motion_states", []))))

with Mantis(sn="BW_XXXXXXX") as robot:
    robot.subscribe_status(on_status)
    robot.left_arm.set_shoulder_pitch(-0.1, block=False)
    robot.wait(robot.left_arm.joint_names, timeout=10.0)
```

常见异常：

| 异常 | 含义和处理 |
| --- | --- |
| `ConnectionError` | 上下文连接失败；确认桥接程序、IP/SN、Zenoh 网络和 `sn` 话题 |
| `RuntimeError: 未连接` | 在 `connect()` 成功前调用了运动接口 |
| `ValueError` | 参数不是有限数值、索引越界、数组长度不为 7 或超时无效 |
| `TimeoutError` | 未收到新鲜状态或机器人端命令在超时时间内未完成；检查状态话题和控制源 |
| `NotImplementedError` | 调用了当前 Standard 配置未提供的能力 |

## 10. 示例

所有示例都在 `examples/` 下按功能分组。会让机器人运动的脚本必须显式
传 `--ip` 或 `--sn`，不会使用硬编码目标。完整索引见
[examples/README.md](./examples/README.md)。

```bash
# 连接和只读上电前检查
python -m examples.basic.connection_example --ip 192.168.50.170
python -m examples.basic.preflight_check_example --ip 192.168.50.170

# 单臂、双臂、IK
python -m examples.arm.joint_control_example --ip 192.168.50.170 --side left
python -m examples.arm.dual_arm_joint_example --ip 192.168.50.170
python -m examples.arm.ik_pose_example --ip 192.168.50.170 --side left --mode rel

# 头部、底盘和安全停止
python -m examples.head.head_example --ip 192.168.50.170
python -m examples.head.head_scan_example --ip 192.168.50.170
python -m examples.chassis.chassis_example --ip 192.168.50.170
python -m examples.chassis.chassis_square_example --ip 192.168.50.170
python -m examples.basic.safe_stop_example --ip 192.168.50.170

# 组合工作流和状态监控
python -m examples.workflows.handoff_workflow_example --ip 192.168.50.170
python -m examples.basic.status_monitor_example --ip 192.168.50.170 --duration 10
```

## 11. 排查清单

| 现象 | 检查项 |
| --- | --- |
| 找不到机器人 | `sdk_bridge.sh` 是否运行；客户端与机器人是否在同一 Zenoh 网络；`sn` 话题是否有消息 |
| 能发现但连接校验超时 | `<SN>/sdk/system_status` 是否持续发布；桥接节点和机器人状态机是否启动 |
| 手臂命令无动作 | 是否使用 `mode:=sdk`、`robot_version:=standard`、`mantis_protocol_version:=v3`；串口和控制源是否正确 |
| IK 失败 | 目标是否使用 `C_Link`；先从 README 的零位参考附近做小增量；查看手臂 command status 的错误信息 |
| 头部或滑台超限 | 检查 `robot.head.limits`、`robot.waist.limits`；默认 `clamp=True` 会截断目标 |
| 底盘停不下来 | 调用 `robot.chassis.stop()`；检查是否有旧进程仍在发布；危险情况使用硬件急停 |
| 多机串控 | 显式传 `--ip` 或 `--sn`，核对 `robot.robot_sn`，确认桥接和 topic 使用同一个 SN |

## 12. 开发验证

```bash
cd standard-SDK
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
python3 -m compileall -q mantis examples tests
python3 -m build
```

许可证见 [LICENSE](./LICENSE)。版本变更见
[RELEASE_NOTES.md](./RELEASE_NOTES.md)。
