import os
import socket
import struct
import time
import threading
import queue

from service.affinity_tool_service import report_event, CURR_EXP_ID
from service.models.affinity_tool_models import EventType
from util.constant import SOCKET_SERVER, SOCKET_PORT, LISTENING
from util.logger import logger

# 协议常量
CMD_HEADER = 0x55AA  # 控制指令帧头 (文档中明确为 0x55AA)
STATUS_HEADER = 0xAA55  # 状态反馈帧头 (文档中明确为 0xAA55)

# 命令字定义
COMMANDS = {
    0: "启动",
    1: "暂停",
    2: "继续",
    3: "停止",
    4: "初始化",
    5: "复位"
}

# 资源状态定义
STATUS_CODES = {
    0: "初始化",
    1: "正常运行",
    2: "警告",
    3: "严重问题",
    4: "错误",
    5: "暂停",
    6: "停止",
    7: "关机"
}

# 全局状态变量
current_status = 7  # 初始状态为关机
status_lock = threading.Lock()
command_queue = queue.Queue()


def udp_listener():
    def udp_listener():
        """监听控制指令的UDP服务"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', int(os.getenv(SOCKET_PORT))))
    logger.info(f"监听控制指令中 (端口 {os.getenv(SOCKET_PORT)})...")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if len(data) < 38:  # 帧头(2)+节点id(8)+类型id(8)+应用id(8)+命令字(4)+时间戳(8)=38字节
                logger.warn(f"收到无效数据包 (长度 {len(data)} 字节)")
                continue

            # 解析控制指令 - 格式: >H(帧头)QQQ(三个8字节id)i(4字节命令字)Q(8字节时间戳)
            header, node_id, type_id, app_id, cmd, timestamp = struct.unpack('>HQQQiQ', data[:38])

            if header != CMD_HEADER:
                logger.warn(f"帧头校验失败: 收到 0x{header:04X}, 期望 0x{CMD_HEADER:04X}")
                continue
            logger.info(f'接收到控制指令：{cmd},长度{len(data)} 字节')

            # 将时间戳转换为可读格式
            human_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1e9))
            cmd_name = COMMANDS.get(cmd, f"未知命令({cmd})")

            # 更新状态
            update_status(cmd)

            # 将命令放入队列供发送线程使用
            command_queue.put((cmd, cmd_name))

        except Exception as e:
            logger.error(f"处理控制指令时出错: {str(e)}")


def update_status(cmd):
    """根据命令更新状态"""
    global current_status
    mapping = {
        0: 1,  # 启动 -> 正常运行
        1: 5,  # 暂停 -> 暂停
        2: 1,  # 继续 -> 正常运行
        3: 6,  # 停止 -> 停止
        4: 0,  # 初始化 -> 初始化
        5: 7  # 复位 -> 关机
    }

    with status_lock:
        current_status = mapping.get(cmd, current_status)
        logger.info(f"状态更新为: {current_status} ({STATUS_CODES[current_status]})")
    report_event(exp_id=CURR_EXP_ID, _type=EventType.CUSTOM_EVENT,
                 message=f'接收到仿真进程控制指令：{COMMANDS.get(cmd)}')


def status_sender():
    """发送状态反馈的UDP服务"""
    """发送状态反馈的UDP服务"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 固定参数 (实际应用中应根据项目要求设置)
    node_id = 0x123456789ABCDEF0
    type_id = 0x00A1B2C3D4E5F678
    app_id = 0x9F8E7D6C5B4A3F21
    resource_name = "SOFTWARE\0".ljust(32, '\0')[:32]  # 确保32字节，以\0结尾
    version = "v1.0.0\0".ljust(16, '\0')[:16]  # 确保16字节，以\0结尾
    update_interval = 2.0  # 固定为2.0秒，与文档要求一致
    architecture = 4  # 其他，与文档一致

    while True:
        try:
            # 获取当前状态和时间戳
            with status_lock:
                status = current_status
            timestamp = time.time_ns()  # 纳秒时间戳，与文档要求一致

            # 构建数据包 - 格式:
            # >H(帧头)QQQ(三个8字节id)32s(资源名称)f(4字节浮点更新周期)
            # 16s(版本号)i(4字节架构)i(4字节状态)Q(8字节时间戳)
            data = struct.pack(
                '>HQQQ32sf16siiQ',
                STATUS_HEADER,
                node_id,
                type_id,
                app_id,
                resource_name.encode('ascii'),
                update_interval,
                version.encode('ascii'),
                architecture,
                status,
                timestamp
            )

            # 发送UDP数据包
            logger.info(f'发送状态反馈到：{os.getenv(SOCKET_SERVER)},{int(os.getenv(SOCKET_PORT))}')
            sock.sendto(data, (os.getenv(SOCKET_SERVER), int(os.getenv(SOCKET_PORT))))

            time.sleep(update_interval)

        except Exception as e:
            logger.warn(f"发送状态反馈时出错: {str(e)}")
            time.sleep(1)


def start_socket_server():
    if int(os.getenv(LISTENING)) == 0:
        return

    # 启动监听线程
    listener_thread = threading.Thread(target=udp_listener, daemon=True)
    listener_thread.start()

    # 启动发送线程
    sender_thread = threading.Thread(target=status_sender, daemon=True)
    sender_thread.start()
