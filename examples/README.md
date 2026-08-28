# Standard SDK 示例

在仓库根目录使用 `python -m examples.<分类>.<脚本>` 运行。会让机器人运动的示例必须显式传 `--ip` 或 `--sn`，所有脚本固定使用 `robot_version=standard`。

## 通用参数

```bash
python -m examples.basic.connection_example --ip 192.168.50.170
python -m examples.basic.connection_example --sn BW_XXXXXXX
```

- `--ip`: Standard 机器人 IP
- `--sn`: 机器人序列号
- `--port`: Zenoh 端口，默认 `7447`
- `--robot-version`: 仅接受 `standard`，通常无需传
- `--verify / --no-verify`: 是否等待机器人状态完成连接校验

## 功能覆盖表

| 功能 | 示例 |
| --- | --- |
| IP/SN 连接、`robot_ip`、`robot_sn`、`system_status` | `basic/connection_example.py` |
| `subscribe_status()` 状态订阅与频率测量 | `basic/status_subscription_example.py` |
| 小幅手臂和头部预览动作 | `basic/rviz_preview_example.py` |
| `RobotDiscovery` 和发现辅助函数 | `discovery/discovery_example.py` |
| 原始 Zenoh `sn` 话题诊断 | `discovery/sn_topic_diagnostic.py` |
| 手臂关节、限位、`home`、`set_joint`、`set_joints`、`block=True/False` | `arm/joint_control_example.py` |
| Standard 命名关节姿态 | `arm/manual_joint_pose_example.py` |
| 机器人端 IK 绝对/相对位姿、左/右/双臂、运动约束 | `arm/ik_pose_example.py` |
| 夹爪 open、close、half_open、set_position | `gripper/gripper_example.py` |
| 头部 look、set_pose、set_pitch、set_yaw、center | `head/head_example.py` |
| Standard C 轴滑台高度、up、down、move、home | `waist/waist_height_example.py` |
| 底盘 forward、backward、strafe、turn、move、stop | `chassis/chassis_example.py` |
| 并行运动与 `robot.wait()` | `workflows/parallel_motion_example.py` |
| 手臂、夹爪、头部组合 workflow | `workflows/coffee_workflow_example.py` |

Standard 腰部不支持前后弯腰，因此没有弯腰示例。

## IK 验收

先用相对小增量验证：

```bash
python -m examples.arm.ik_pose_example \
  --ip 192.168.50.170 \
  --side left \
  --mode rel
```

验证双臂并行：

```bash
python -m examples.arm.ik_pose_example \
  --ip 192.168.50.170 \
  --side both \
  --mode both \
  --non-blocking \
  --max-velocity 1.0 \
  --max-acceleration 3.0 \
  --max-jerk 20.0
```

绝对位姿使用 `C_Link` 坐标。示例内置的是 Standard 零关节角下左右 Degree7 原点位姿，不是旧 Mantis 机型坐标。

`--non-blocking` 会以 `block=False` 发送命令，再调用 `robot.wait()` 等待对应 `command_id` 完成。IK 在机器人 ROS 侧求解，客户端不需要 Pinocchio、CasADi 或 URDF。
