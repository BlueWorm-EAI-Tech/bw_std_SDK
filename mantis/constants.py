"""Standard 机器人的公共名称、限位和 Zenoh topic 常量。

这里的常量是 SDK 与机器人端桥接程序之间的协议边界。角度统一使用
弧度，长度统一使用米；区间均为闭区间，文档中使用 ``下限 ~ 上限``
表示可以取到两端值。手臂的公共名称保持人体语义，发布到 Standard
机器人端时再映射为 ``A_<side>_DegreeN_joint``，其中 N 为 1 ~ 7。
"""

# SDK 公共语义名。索引 0 ~ 6 依次对应 Standard Degree1 ~ Degree7。
# 这些名称用于 Python API、system_status 查询和 wait() 参数，不是 ROS
# 侧的正式 URDF 名称；映射关系见 SERIAL_TO_URDF_MAP。
LEFT_ARM_JOINTS = [
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_pitch_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
]

RIGHT_ARM_JOINTS = [
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_pitch_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]

JOINT_NAMES = LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS
NUM_ARM_JOINTS = 7
NUM_TOTAL_JOINTS = 14

# 数据来源：机器人端 bw_core/assets/standard_ik/standard_ik.urdf。
# 每一项都是闭区间 (最小值, 最大值)，单位为 rad。
LEFT_ARM_LIMITS = [
    (-2.069, 1.022),  # Degree1: shoulder_pitch
    (-0.142, 2.077),  # Degree2: shoulder_roll
    (-1.541, 1.541),  # Degree3: shoulder_yaw
    (-0.529, 1.355),  # Degree4: elbow_pitch
    (-1.540, 1.540),  # Degree5: wrist_roll
    (-0.756, 0.756),  # Degree6: wrist_pitch
    (-1.017, 1.018),  # Degree7: wrist_yaw
]

RIGHT_ARM_LIMITS = [
    (-2.069, 1.022),  # Degree1: shoulder_pitch
    (-2.077, 0.142),  # Degree2: shoulder_roll
    (-1.541, 1.541),  # Degree3: shoulder_yaw
    (-0.529, 1.355),  # Degree4: elbow_pitch
    (-1.540, 1.540),  # Degree5: wrist_roll
    (-0.756, 0.756),  # Degree6: wrist_pitch
    (-1.017, 1.018),  # Degree7: wrist_yaw
]

# 与 Standard v3 串口出口及 VR 链路一致，单位为 rad。
HEAD_LIMITS = {
    "pitch": (-0.785, 0.524),
    "yaw": (-1.570, 1.570),
}

GRIPPER_LIMITS = (0.0, 1.0)

LEFT_ARM_URDF_JOINTS = [
    f"A_left_Degree{index}_joint" for index in range(1, 8)
]
RIGHT_ARM_URDF_JOINTS = [
    f"A_right_Degree{index}_joint" for index in range(1, 8)
]
URDF_ARM_JOINT_NAMES = LEFT_ARM_URDF_JOINTS + RIGHT_ARM_URDF_JOINTS

ALL_URDF_JOINTS = [
    "C_joint",
    *URDF_ARM_JOINT_NAMES,
    "A_left_Degree8_joint",
    "A_left_Degree9_joint",
    "A_right_Degree8_joint",
    "A_right_Degree9_joint",
]

# SDK 语义名 -> Standard URDF 正式关节名。
SERIAL_TO_URDF_MAP = dict(zip(JOINT_NAMES, URDF_ARM_JOINT_NAMES))


class Topics:
    """按机器人 SN 隔离的 Zenoh topic 后缀。

    除 ``sn`` 外，实际使用的话题格式都是 ``<SN>/sdk/<name>``。
    使用 SN 前缀可以让同一局域网内的多个机器人共享 Zenoh 网络时，
    控制命令和状态不会串到其他机器人。
    """

    SDK_JOINT_STATES = "sdk/joint_states"
    SDK_ARM_COMMAND = "sdk/arm_command"
    SDK_ARM_COMMAND_STATUS = "sdk/arm_command_status"
    SDK_CHASSIS = "sdk/chassis"
    SDK_PELVIS_HEIGHT = "sdk/pelvis_height"
    # 保留协议键；Standard 不支持腰部前后弯腰。
    SDK_WAIST_ANGLE = "sdk/waist_angle"
    SYSTEM_STATUS = "sdk/system_status"
    FORCE_FEEDBACK = "sdk/force_feedback"
    ROBOT_IDENTITY = "sn"
