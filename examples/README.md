# Standard SDK 示例

在仓库目录执行 `python3 -m examples.<分类>.<脚本>`。
NUC 先切 SDK，确认双臂零位姿态稳定；切模式本身会运动。客户端与机器人位于同一局域网，默认端口 `7447`。

## 通用参数

| 参数 | 含义 |
| --- | --- |
| `--ip` / `--sn` | 机器人 IP / 实际 SN；动作示例至少传一个 |
| `--port` | Zenoh 端口，默认 7447 |
| `--robot-version` | `standard`，通常不需要传 |
| `--verify` / `--no-verify` | 连接时是否校验状态，默认校验 |
| `--non-blocking` | 支持此参数的示例发送后显式等待 |

默认 `block=True`；`block=False` 后用模块 `wait()` 或 `robot.wait()` 等待。
运行 `python3 -m examples.<分类>.<脚本> --help` 查看该示例参数。

## 功能覆盖表

| 示例 | 作用 |
| --- | --- |
| `basic.connection_example` | 连接并显示身份和状态，只读 |
| `basic.preflight_check_example` | 上电前检查：SN、IP、状态字段，只读 |
| `basic.status_subscription_example` | `subscribe_status` 状态订阅和频率，只读 |
| `basic.status_monitor_example` | 状态监控，只读 |
| `discovery.discovery_example` | 发现机器人，只读 |
| `discovery.sn_topic_diagnostic` | 读取身份话题，只读 |
| `arm.joint_control_example` | 单臂手臂关节控制，`--side left/right` |
| `arm.dual_arm_joint_example` | 双臂关节目标与等待 |
| `arm.manual_joint_pose_example` | 用关节名称组合姿态 |
| `arm.ik_pose_example` | IK，`--side left/right/both --mode abs/rel/both`，可设置运动约束 |
| `gripper.gripper_example` | 夹爪，`--side left/right/both --position 0~1`，结束默认张开 |
| `head.head_example` | 头部三轴控制 |
| `head.head_scan_example` | 头部扫描 |
| `waist.waist_height_example` | 滑台升降与回零 |
| `chassis.chassis_example` | 底盘平移、旋转和速度设置 |
| `chassis.chassis_square_example` | 底盘方形路径 |
| `basic.safe_stop_example` | 底盘安全停止；此示例会先移动底盘 |
| `workflows.parallel_motion_example` | 多模块并行 |
| `workflows.coffee_workflow_example` | 多步骤 workflow |
| `workflows.handoff_workflow_example` | 双侧夹爪交接 |

## 常用命令

```bash
python3 -m examples.basic.connection_example --ip 192.168.1.100
python3 -m examples.basic.preflight_check_example --ip 192.168.1.100
python3 -m examples.arm.joint_control_example --ip 192.168.1.100 --side left
python3 -m examples.arm.ik_pose_example --ip 192.168.1.100 --side right --mode rel --max-velocity 0.2 --max-acceleration 0.5 --max-jerk 2
python3 -m examples.gripper.gripper_example --ip 192.168.1.100 --side left --position 0.5 --hold 0.5
python3 -m examples.basic.status_monitor_example --ip 192.168.1.100 --duration 10
```

除连接、发现和状态示例外，示例会执行一组动作；参数、单位和范围见主 README。
夹爪示例仅操作所选侧，结束默认张开；张开不等于电机卸力。
