import time
import math
from math import pi as PI
import traceback
import sys
sys.path.append('D:\\vs2019ws\\PythonCtt\\PythonCtt')
from schemas.response import resp

try:
    import jkrc
except ImportError:
    print("The jkrc library is not available.")
    jkrc = None  # 如果没有找到模块，可以设置为 None 或其他默认值，避免后续代码崩溃

robotIp = "10.5.5.100"
class JakaFunction:

    @classmethod
    async def power_on(cls):
        robot = jkrc.RC(robotIp)  # 返回一个机器人对象
        robot.login()  # 登录
        robot.power_on()  # 上电
        result = 'power success'
        return result

    @classmethod
    async def enable_robot(cls):
        robot = jkrc.RC(robotIp)  # 返回一个机器人对象
        robot.enable_robot()

    @classmethod
    #手动控制按钮启动
    async def jog_start(cls, aj_num, move_mode, coord_type, jog_vel, pos_cmd):


        robot = jkrc.RC(robotIp)  # 返回一个机器人对象
        robot.jog(aj_num, move_mode, coord_type, jog_vel, pos_cmd)
        time.sleep(2)
        robot.jog_stop()

    @classmethod
    # 手动控制按钮关闭
    async def jog_Car(cls, aj_num, move_mode, coord_type, jog_vel, pos_cmd):
        robot = jkrc.RC(robotIp)  # 返回一个机器人对象
        robot.jog(aj_num=aj_num, move_mode=move_mode, coord_type=coord_type, jog_vel=jog_vel, pos_cmd=pos_cmd)  #aj_num正方向运动pos_cmd
        robot.jog_stop()
        """
            aj_num：axis_joint_based 标识值，在关节空间下代表轴号，1 轴到六轴的轴号分别对应数字 0 到 5，笛卡尔空间下依次为 x，y，z，rx，ry，rz 分别对应数字 0 到 5
            move_mode：0 代表绝对运动，1 代表增量运动，2 代表连续运动
            coord_type：机器人运动坐标系，工具坐标系，基坐标系（当前的世界/用户坐标系）或关节空间
            jog_vel：指令速度，旋转轴或关节运动单位为 rad/s，移动轴单位为 mm/s，速度的正负决定运动方向的正负。
            pos_cmd：指令位置，旋转轴或关节运动单位为 rad，移动轴单位为 mm，当 move_mdoe 是绝对运动时参数可忽略
        """

    @classmethod
    # 末端圆弧运动
    async def circular_move_extend(cls, start_pos, end_pos, mid_pos, speed, acc, tol, cricle_cnt):
        _ABS = 0
        _BLOCK = 1
        try:
            robot = jkrc.RC(robotIp)
            robot.joint_move([0] + [PI * 0.5] * 3 + [PI * -0.5, 0], 0, 1, 200)
            robot.linear_move(start_pos, _ABS, _BLOCK, 50)
            robot.circular_move_extend(end_pos, mid_pos, _ABS, _BLOCK, speed, acc, tol, cricle_cnt, None)

        except Exception:
            traceback.print_exc()

    @classmethod
    # 紧急停止
    async def motion_abort(cls):
        robot = jkrc.RC(robotIp)
        robot.motion_abort()


