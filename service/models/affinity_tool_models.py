from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Dict

import numpy as np

from affinity.models import SingleSchedulerPlan, Communication
from util.kuber_api import nodes_with_label


@dataclass
class Agent:
    agent_sid: str


@dataclass
class NodeAgentsInfo:
    node_sid: str
    agents: List[Agent] = field(default_factory=list)

    @staticmethod
    def load(plans: list[SingleSchedulerPlan]) -> List['NodeAgentsInfo']:
        # 按节点分组聚合数据
        node_agents_map: Dict[str, List[Agent]] = {}

        for _plan in plans:
            node_sid = nodes_with_label.get(_plan.scheduled_node)
            agent_sid = _plan.pod  # 假设 pod 名称即为 agent_sid

            if node_sid not in node_agents_map:
                node_agents_map.__setitem__(node_sid, [])

            node_agents_map[node_sid].append(Agent(agent_sid=agent_sid))

        # 转换为 NodeAgentsInfo 对象列表
        return [
            NodeAgentsInfo(node_sid=node_sid, agents=agents)
            for node_sid, agents in node_agents_map.items()
        ]


@dataclass
class InteractionDetail:
    source_agent: str
    target_agent: str
    traffic: str
    frequency: str

    @staticmethod
    def load(comm_data: list[Communication]) -> List['InteractionDetail']:
        interaction_details = []

        for comm in comm_data:
            # 计算 traffic 并保留两位小数
            traffic = ""
            if comm.package is not None and comm.freq is not None and comm.freq != 0:
                traffic_value = (1 / comm.freq) * comm.package
                traffic = f"{traffic_value:.2f} MB/s"  # 保留两位小数

            # 使用 Communication 对象的属性构建 InteractionDetail
            detail = InteractionDetail(
                source_agent=comm.src_pod if comm.src_pod is not None else "",
                target_agent=comm.tgt_pod if comm.tgt_pod is not None else "",
                traffic=traffic,
                frequency=str(comm.freq) if comm.freq is not None else ""
            )
            interaction_details.append(detail)

        return interaction_details

        return interaction_details


@dataclass
class AffinityValue:
    source_agent: str
    target_agent: str
    affinity_value: str

    @staticmethod
    def load(pod_affinity: np.ndarray, idx2pod: dict):
        affinity_values = []
        n = pod_affinity.shape[0]
        # 创建反向映射 {index: pod_name}
        pod2idx_reverse = {v: k for k, v in idx2pod.items()}

        for i in range(n):
            for j in range(i, n):  # 只遍历上三角矩阵避免重复
                value = pod_affinity[i, j]
                if value != 0:  # 只记录非零值
                    value_str = f"{value:.6f}".rstrip('0').rstrip('.') if '.' in f"{value:.6f}" else str(value)
                    affinity_values.append(
                        AffinityValue(
                            source_agent=pod2idx_reverse[i],  # 使用反向映射
                            target_agent=pod2idx_reverse[j],
                            affinity_value=value_str
                        )
                    )

        return affinity_values


@dataclass
class ExperimentData:
    exp_id: int
    node_agents_info: List[NodeAgentsInfo] = field(default_factory=list)
    interaction_detail: List[InteractionDetail] = field(default_factory=list)
    affinity_values: List[AffinityValue] = field(default_factory=list)
    gather_at: Optional[int] = None


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

    CUSTOM_EVENT = 17
    """仿真进程控制指令"""

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
            16: "亲和性调度频率",
            17: "仿真进程控制指令"
        }
        return descriptions.get(value, "未知事件类型")
