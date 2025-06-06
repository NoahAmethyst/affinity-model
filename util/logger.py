import datetime
import json
import logging
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import coloredlogs
import http.client

from util.constant import AFFINITY_SERVER
from util.time_util import now_millis

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(name='affinity-model')
coloredlogs.install(logger=logger)
logger.propagate = False


def init_logger():
    ## Setup logger color
    coloredFormatter = coloredlogs.ColoredFormatter(
        fmt='[%(name)s] %(asctime)s %(funcName)s %(lineno)-3d  %(message)s',
        level_styles=dict(
            debug=dict(color='white'),
            info=dict(color='green'),
            warning=dict(color='yellow', bright=True),
            error=dict(color='red', bold=True, bright=True),
            critical=dict(color='black', bold=True, background='red'),
        ),
        field_styles=dict(
            name=dict(color='white'),
            asctime=dict(color='white'),
            funcName=dict(color='white'),
            lineno=dict(color='white'),
        )
    )

    ## Setup logger streamHandler
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(fmt=coloredFormatter)
    logger.addHandler(hdlr=ch)
    logger.setLevel(level=logging.DEBUG)


class EventType(IntEnum):
    """试验事件类型枚举"""
    EXPERIMENT_START = 1
    """试验开始"""

    STATIC_SCHEDULING_START = 2
    """开始静态调度"""

    STATIC_AFFINITY_SCORING_START = 3
    """开始静态亲和性评分"""

    STATIC_AFFINITY_SCORING_COMPLETE = 4
    """静态亲和性评分完成"""

    STATIC_SCHEDULING_POLICY_GENERATION_START = 5
    """开始生成静态亲和性调度策略"""

    SCHEDULING_POLICY_GENERATION_COMPLETE = 6
    """调度策略生成完成"""

    STATIC_SCHEDULING_POLICY_EXECUTION = 7
    """执行静态调度策略"""

    SIMULATION_SOLUTION_TIME_COLLECTION_START = 8
    """开始采集仿真系统解算时间"""

    AGENT_COMMUNICATION_RELATION_CHANGE = 9
    """智能体通信关系变化"""

    DYNAMIC_AFFINITY_SCORING_START = 10
    """开始动态亲和性评分"""

    DYNAMIC_AFFINITY_SCORING_COMPLETE = 11
    """动态亲和性评分完成"""

    DYNAMIC_SCHEDULING_POLICY_GENERATION_START = 12
    """开始生成动态亲和性调度策略"""

    DYNAMIC_SCHEDULING_POLICY_COMPLETE = 13
    """动态亲和性调度策略完成"""

    DYNAMIC_SCHEDULING_POLICY_EXECUTION = 14
    """执行动态调度策略"""

    EXPERIMENT_END = 15
    """试验结束"""

    AFFINITY_SCHEDULING_FREQUENCY = 16
    """亲和性调度频率"""

    @classmethod
    def get_description(cls, value: int) -> str:
        """获取枚举值的描述文本"""
        descriptions = {
            1: "试验开始",
            2: "开始静态调度",
            3: "开始静态亲和性评分",
            4: "静态亲和性评分完成",
            5: "开始生成静态亲和性调度策略",
            6: "调度策略生成完成",
            7: "执行静态调度策略",
            8: "开始采集仿真系统解算时间",
            9: "智能体通信关系变化",
            10: "开始动态亲和性评分",
            11: "动态亲和性评分完成",
            12: "开始生成动态亲和性调度策略",
            13: "动态亲和性调度策略完成",
            14: "执行动态调度策略",
            15: "试验结束",
            16: "亲和性调度频率"
        }
        return descriptions.get(value, "未知事件类型")


def report_event(exp_id: int, _type: EventType, message: Optional[str] = None,
                 duration: Optional[int] = None):
    _host = os.getenv(AFFINITY_SERVER)
    conn = http.client.HTTPConnection(_host, 9553)
    payload = json.dumps({
        "exp_id": exp_id,
        "type": message,
        "message": message,
        "trigger_at": now_millis(),
        "duration": duration
    })
    headers = {
        'Content-Type': 'application/json'
    }
    logger.info(f'report event:{EventType.get_description(_type.value)}')
    conn.request("POST", "/api/affinity_tools/exp/loggers/create", payload, headers)
    res = conn.getresponse()
    data = res.read()
    logger.info(f'report event get response:{data.decode("utf-8")}')
