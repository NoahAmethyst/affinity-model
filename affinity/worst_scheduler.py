import copy
import math

import numpy as np

from affinity import BasePod, Graph, MultiStageScheduler, read_excel_and_construct_agents, read_excel_and_generate_yamls
from affinity.dynamic_schedule import set_last_plan
from affinity.models import BaseNode, Communication
from affinity.offline_scheduler import Scheduler
from affinity.schedule_operator import operate_schedule
from service import affinity_tool_service
from service.models import affinity_tool_models
from util.logger import logger
from util.time_util import now_millis


class WorstFitScheduler(Scheduler):
    def __init__(self, pods_data, nodes_data, pod_affinity, node_affinity):
        super().__init__(pods_data, nodes_data, pod_affinity, node_affinity)
        self.scheduler_name = "worst_fit_scheduler"

    def schedule(self) -> np.ndarray:
        """ 考虑gpu优先 """
        pods = self.pods
        nodes = copy.deepcopy(self.nodes)
        gpu_nodes_idx = []
        normal_nodes_idx = []
        for idx, node in enumerate(nodes):
            if node.gpu > 0:
                gpu_nodes_idx.append(idx)
            else:
                normal_nodes_idx.append(idx)
        plan = np.zeros(len(self.pods), dtype=int)

        for i, pod in enumerate(pods):
            place_node = None
            min_value = math.inf
            if pod.gpu == 0:  # 优先从普通节点选择
                for j in normal_nodes_idx:
                    node = nodes[j]
                    v = node.max_usage(pod)
                    if node >= pod and min_value > v and 1 >= v:  # node资源比pod多最少的节点
                        min_value = v
                        place_node = j
            if place_node is not None:  # 找到了，直接返回
                plan[i] = place_node
                nodes[place_node] = nodes[place_node] - pod
                continue
            for j in gpu_nodes_idx:  # 从gpu节点找
                node = nodes[j]
                v = node.max_usage(pod)
                if node >= pod and min_value > v and 1 >= v:  # node资源比pod多最少的节点
                    min_value = v
                    place_node = j
            if place_node is None:
                logger.warn('fail to place pods')
                return None
            plan[i] = place_node
            nodes[place_node] = nodes[place_node] - pod
        self.plan = plan
        return plan

    def schedule_without_gpu(self) -> np.ndarray:
        """ 不考虑gpu """
        pods = self.pods
        nodes = copy.deepcopy(self.nodes)
        plan = np.zeros(len(self.pods), dtype=int)

        for i, pod in enumerate(pods):
            place_node = None
            min_value = math.inf
            for j, node in enumerate(nodes):
                v = node.max_usage(pod)
                if min_value > v and 1 >= v:  # node资源比pod多最少的节点
                    min_value = v
                    place_node = j
            if place_node is None:
                logger.warn('fail to place pods')
                return None
            plan[i] = place_node
            nodes[place_node] = nodes[place_node] - pod
        self.plan = plan
        return plan


def worst_schedule(exp_id: int, pods_data: list[BasePod], pod2idx: dict[str, int], nodes_data: list[BaseNode],
                    comm_data: list[Communication]):
    g = Graph(pods_data=pods_data, pod2idx=pod2idx, comm_data=comm_data, nodes_data=nodes_data)
    # 上报静态调度开始事件
    affinity_tool_service.report_event(exp_id=exp_id,
                                       message=f'本次静态调度涉及智能体{len(g.pods)}个,配置{len(g.nodes)}个调度节点',
                                       _type=affinity_tool_models.EventType.STATIC_SCHEDULING_START)

    # 上报开始静态亲和性评分事件
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.STATIC_AFFINITY_SCORING_START)

    _start = now_millis()
    pod_affinity, node_affinity = g.cal_affinity()
    _end = now_millis()
    # 上报完成静态亲和性评分事件
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.STATIC_AFFINITY_SCORING_COMPLETE,
                                       duration=_end - _start)

    scheduler = WorstFitScheduler(pods_data=pods_data, nodes_data=nodes_data, pod_affinity=pod_affinity,
                                  node_affinity=node_affinity)


    # 上报开始生成静态亲和性调度策略
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.STATIC_SCHEDULING_POLICY_GENERATION_START,
                                       duration=_end - _start)
    ### schedule
    _start = now_millis()
    _plan = scheduler.schedule()
    ### check
    ### schedule
    _plan = scheduler.schedule()

    ### check
    plan = scheduler.check_and_gen(scheduler, _plan)
    _end = now_millis()
    # 上报完成静态亲和性调度策略的生成

    # 同步亲和性调度详情数据
    affinity_tool_service.sync_agents_graph(
        affinity_tool_service.build_exp_data(exp_id=exp_id, plans=plan, comm_data=comm_data, pod_affinity=pod_affinity,
                                             pods=pods_data))

    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.SCHEDULING_POLICY_GENERATION_COMPLETE,
                                       duration=_end - _start)

    agents = read_excel_and_construct_agents(pods_data, plan)
    deploys = read_excel_and_generate_yamls(agents, comm_data)

    # 上报执行调度策略
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.STATIC_SCHEDULING_POLICY_EXECUTION,
                                       duration=_end - _start)
    operate_schedule(exp_id=exp_id, deploys=deploys)

    # 记录上一轮调度计划
    set_last_plan(plan)