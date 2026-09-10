# Standard SDK 示例

在仓库根目录执行 `python -m examples.<分类>.<脚本>`。除只读的发现、连接
和状态示例外，所有脚本都会让真实机器人运动，必须显式传入 `--ip` 或
`--sn`，不会使用硬编码目标。

## 运行前检查

1. 机器人端已启动 `./scripts/local/sdk_bridge.sh standard v3 wifi`（有线网络使用 `wired`）。
2. 客户端和机器人在同一 Zenoh 网络，且默认端口 `7447` 可达。
3. 急停可用、运动区域无人且无障碍物；第一次运行使用较小的位移和较低速度。
4. 先运行 `basic/preflight_check_example.py` 确认 SN、IP 和状态字段，再运行运动示例。

## 通用参数

```bash
python -m examples.basic.connection_example --ip 192.168.50.170
python -m examples.basic.connection_example --sn BW_XXXXXXX
```

| 参数 | 说明 |
| --- | --- |
| `--ip` | Standard 机器人 IP；与 `--sn` 至少传一个（连接示例可自动发现） |
| `--sn` | 机器人序列号；多机器人环境优先使用 |
| `--port` | Zenoh router 端口，默认 `7447` |
| `--robot-version` | 只接受 `standard`，通常不需要传 |
| `--verify` / `--no-verify` | 是否等待 `system_status` 完成连接校验，默认开启 |
| `--non-blocking` | 支持该参数的示例使用 `block=False`，结尾显式等待 |

## 功能覆盖表

下面的索引按 SDK 公共能力列出示例；脚本内的 `subscribe_status`、
`block=True`、`block=False` 和 `robot.wait()` 用法都对应真实 API。

### 连接、发现和诊断

| 示例 | 作用 | 是否运动 |
| --- | --- | --- |
| `basic/connection_example.py` | 按 IP/SN 或自动发现连接，打印 `robot_ip`、`robot_sn`、`system_status` | 否 |
| `basic/preflight_check_example.py` | 只读上电前检查：身份、状态字段、运动标志和支持能力 | 否 |
| `basic/status_subscription_example.py` | 订阅状态并测量消息频率 | 否 |
| `basic/status_monitor_example.py` | 状态监控：持续打印状态变化和当前运动部件 | 否 |
| `discovery/discovery_example.py` | `RobotDiscovery` 增量发现和在线超时剔除 | 否 |
| `discovery/sn_topic_diagnostic.py` | 直接读取并解析 `sn` 话题，定位网络或身份问题 | 否 |

### 手臂、IK 和夹爪

| 示例 | 作用 |
| --- | --- |
| `arm/joint_control_example.py` | 单臂单关节、7 轴目标、限位、速度和阻塞模式 |
| `arm/dual_arm_joint_example.py` | 双臂同时发送 7 轴目标，演示 command id 等待 |
| `arm/manual_joint_pose_example.py` | 使用 `shoulder_pitch` 等可读方法组合小姿态 |
| `arm/ik_pose_example.py` | Standard `C_Link` 下的绝对/相对 IK、双臂和运动约束 |
| `gripper/gripper_example.py` | `open`、`close`、`half_open` 和 `set_position` |

### 头部、滑台和底盘

| 示例 | 作用 |
| --- | --- |
| `head/head_example.py` | `look_*`、`set_pose`、回中和限位读取 |
| `head/head_scan_example.py` | 在安全范围内按多个 yaw 目标扫描，演示观察状态 |
| `waist/waist_height_example.py` | C 轴滑台回零、升降、相对位移和限位 |
| `chassis/chassis_example.py` | 全向平移、旋转、摩擦补偿和非阻塞停止 |
| `chassis/chassis_square_example.py` | 底盘方形路径：四段短距离路径，演示每段完成后再执行下一段 |
| `basic/safe_stop_example.py` | `try/finally` 和 Ctrl-C 时发送底盘零速度 |

### 组合工作流

| 示例 | 作用 |
| --- | --- |
| `workflows/parallel_motion_example.py` | 手臂、头部、夹爪、滑台非阻塞并行，最后 `robot.wait()` |
| `workflows/coffee_workflow_example.py` | 手臂、夹爪、头部和回零的完整多步骤示例 |
| `workflows/handoff_workflow_example.py` | 两侧夹爪交接的可读工作流，展示阶段化函数和异常清理 |

## 常用命令

```bash
# 先做只读检查
python -m examples.basic.preflight_check_example --ip 192.168.50.170

# 双臂小幅度运动
python -m examples.arm.dual_arm_joint_example --ip 192.168.50.170

# 只做相对 IK 小增量
python -m examples.arm.ik_pose_example \
  --ip 192.168.50.170 --side left --mode rel

# 双臂非阻塞 IK，并覆盖机器人端运动约束
python -m examples.arm.ik_pose_example \
  --ip 192.168.50.170 --side both --mode both --non-blocking \
  --max-velocity 1.0 --max-acceleration 3.0 --max-jerk 20.0

# 查看状态和底盘安全停止
python -m examples.basic.status_monitor_example --ip 192.168.50.170 --duration 10
python -m examples.basic.safe_stop_example --ip 192.168.50.170
```

## 示例编写规范

- 使用 `from examples.common import ...` 复用连接、参数和目标校验。
- 所有真实运动都使用 `with connected_robot(args)`，保证异常时断开连接。
- 目标参数放在命令行，不在代码中写入真实 IP、SN 或永久循环。
- 非阻塞命令必须在结尾调用模块 `wait()` 或 `robot.wait()`；底盘示例还应在 `finally` 中调用 `stop()`。
- 示例中的距离、角度和速度与 README 一样使用明确单位；范围统一写成 `下限 ~ 上限`。
- Standard 没有腰部前后弯腰轴，不添加弯腰示例；调用相应 API 会得到 `NotImplementedError`。
