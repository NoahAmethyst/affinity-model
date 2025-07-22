import time
import numpy as np
import service.affinity_tool_service as affinity_tool_service
import service.models.affinity_tool_models as affinity_tool_models
from affinity.calculate import Graph
from affinity.models import Node, SingleSchedulerPlan, BasePod, BaseNode, Communication
from affinity.parse_schedule import read_excel_and_construct_agents, read_excel_and_generate_yamls
from affinity.schedule_operator import operate_schedule
from util.time_util import now_millis

last_plan: list[SingleSchedulerPlan] = []


def set_last_plan(_plan: list[SingleSchedulerPlan]):
    last_plan = _plan


def load_node_resource(resource_data):
    nodes: list[Node] = []
    for idx, row in resource_data.iterrows():
        nodes.append(Node(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
    return nodes


def new_nodes(resource_data: list[Node], pod_nodes_data: list[SingleSchedulerPlan]) -> dict[str:Node]:
    nodes = {}

    for _node in resource_data:
        nodes.__setitem__(_node.name, _node)

    agents = {}
    for _pod_node in pod_nodes_data:
        if agents.get(_pod_node.scheduled_node) is None:
            agents.setdefault(_pod_node.scheduled_node, [])
        agents[_pod_node.scheduled_node].append(_pod_node.pod)

    for _node in agents.keys():
        nodes[_node].set_running_agents(agents.get(_node))

    return nodes


def get_affinity_score(nodes: dict[str:Node], agent: str, affinity) -> list:
    scores = []
    sk = get_affinity_key(agent)

    for node_name in nodes.keys():
        score = 0
        for pod in nodes[node_name].agents:
            tk = get_affinity_key(pod)
            score += affinity[sk][tk]
        scores.append(score)

    return scores


def get_affinity_key(name: str) -> int:
    return int(name.split("-")[1]) - 1


def get_resource_usage(nodes: dict[str:Node], cpu, memory, gpu, disk) -> list:
    res = []

    for node_name in nodes.keys():
        if nodes[node_name].cpu_free < cpu or nodes[node_name].memory_free < memory:
            res.append(0)
            continue

        res.append((nodes[node_name].cpu_used + cpu) / (nodes[node_name].cpu_used + nodes[node_name].cpu_free))

    return res


def get_schedule_node(nodes: dict[str:Node], affinity_score: list) -> str:
    _node_name = []

    for _node in nodes.keys():
        _node_name.append(_node)

    score = np.array(affinity_score)

    return _node_name[np.argmax(score)]


def update_nodes(nodes: dict[str:Node], scheduled_node: str, cpu, memory, gpu, disk, name):
    nodes[scheduled_node].cpu_free -= cpu
    nodes[scheduled_node].memory_free -= memory
    nodes[scheduled_node].agents.append(name)


def dynamic_plan(node_resource: list[Node], pods: list[BasePod], last_pods_affinity) -> list[SingleSchedulerPlan]:
    _plan: list[SingleSchedulerPlan] = []
    nodes = new_nodes(resource_data=node_resource, pod_nodes_data=last_plan)
    affinity = last_pods_affinity
    for _pod in pods:
        affinity_score = get_affinity_score(nodes, _pod.name, affinity)
        scheduled_node = get_schedule_node(nodes=nodes, affinity_score=affinity_score)
        update_nodes(nodes, scheduled_node, _pod.cpu, _pod.mem, _pod.gpu, _pod.disk, _pod.name)
        _plan_ = SingleSchedulerPlan(pod=_pod.name, scheduled_node=scheduled_node)
        _plan.append(_plan_)

        last_plan.append(_plan_)

    return _plan


# 修改pods.csv对智能体的添加,删除的话不能在这里体现，不然就亲和性index就乱了，删除pod把它从通信关系csv里面删除就好
def dynamic_schedule(exp_id: int, pods_data: list[BasePod], pod2idx: dict[str, int], nodes_data: list[BaseNode],
                     comm_data: list[Communication],
                     new_pods: list[BasePod], node_resource: list[Node]):
    time.sleep(1)
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.AGENT_COMMUNICATION_RELATION_CHANGE)
    time.sleep(1)
    g = Graph(pods_data=pods_data, pod2idx=pod2idx, comm_data=comm_data, nodes_data=nodes_data)
    # 上报动态亲和性评分
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.DYNAMIC_AFFINITY_SCORING_START)

    _start = now_millis()
    pod_affinity, _ = g.cal_affinity()
    _end = now_millis()
    # 上报完成动态亲和性评分事件
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.DYNAMIC_AFFINITY_SCORING_COMPLETE,
                                       duration=_end - _start)

    time.sleep(1)
    # 上报生成动态亲和性策略
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.DYNAMIC_SCHEDULING_POLICY_GENERATION_START)
    _start = now_millis()
    plan = dynamic_plan(node_resource, new_pods, pod_affinity)
    _end = now_millis()
    # 上报完成动态亲和性策略
    # affinity_tool_service.report_plan(exp_plan=plan)
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.DYNAMIC_SCHEDULING_POLICY_COMPLETE,
                                       duration=_end - _start)

    time.sleep(1)
    affinity_tool_service.sync_agents_graph(
        affinity_tool_service.build_exp_data(exp_id=exp_id, plans=plan, comm_data=comm_data, pod_affinity=pod_affinity,
                                             pods=pods_data))

    agents = read_excel_and_construct_agents(pods_data, plan)
    deploys = read_excel_and_generate_yamls(agents, comm_data)

    # 上报执行动态调整策略
    affinity_tool_service.report_event(exp_id=exp_id,
                                       _type=affinity_tool_models.EventType.DYNAMIC_SCHEDULING_POLICY_EXECUTION)
    operate_schedule(exp_id=exp_id, deploys=deploys)
