from io import BytesIO
from typing import Optional

import pandas as pd
from fastapi import BackgroundTasks

from affinity.calculate import Graph, load_pods, load_nodes, load_comm
from affinity.dynamic_schedule import dynamic_schedule, load_node_resource
from affinity.models import SingleSchedulerPlan, BasePod, Communication
from affinity.multi_stage_scheduler import MultiStageScheduler, static_schedule
from affinity.parse_schedule import read_excel_and_construct_agents, read_excel_and_generate_yamls
from affinity.schedule_operator import STOPED_EXP
from util.kuber_api import init_nodes_with_label
from util.logger import logger
import sched
import time

scheduler = sched.scheduler(time.time, time.sleep)


def exec_schedule(exp_id: int, contents):
    logger.info(f'start static schedule，exp_id:{exp_id}')

    file_obj = BytesIO(contents)
    _comm_excel = pd.read_excel(io=file_obj,
                                sheet_name='communication')
    _nodes_resources_excel = pd.read_excel(io=file_obj,
                                           sheet_name='d-node_resource')

    _nodes_excel = pd.read_excel(io=file_obj,
                                 sheet_name='nodes')

    _pods_excel = pd.read_excel(io=file_obj,
                                sheet_name='pods')

    _pods_data, _pod2idx = load_pods(pods_excel=_pods_excel)

    nodes_data = load_nodes(nodes_excel=_nodes_excel)

    # 根据nodes_data设置的label初始化映射的node name
    for _node in nodes_data:
        init_nodes_with_label(_node.name)

    _comm_data = load_comm(comm_excel=_comm_excel)

    comm_data: list[Communication] = []

    pods_data: list[BasePod] = []

    _task_pods: dict[int, list[BasePod]] = {}
    _task_comm: dict[int, list[Communication]] = {}

    pod2idx: dict[str, int] = {}
    # 静态调度过滤掉动态调度中智能体变化数据
    # 只过滤新增，不过滤删除
    for _pod in _pods_data:
        if _pod.change_type:
            if _task_pods.get(_pod.delay) is None:
                _task_pods.__setitem__(_pod.delay, [])
            _task_pods[_pod.delay].append(_pod)

        else:
            pods_data.append(_pod)
            pod2idx.__setitem__(_pod.name, _pod2idx.get(_pod.name))

        if _pod.change_type == '-':
            pods_data.append(_pod)
            pod2idx.__setitem__(_pod.name, _pod2idx.get(_pod.name))

    # 静态调度过滤掉动态调度中交互关系变化数据,只过滤新增，不过滤删除
    for _comm in _comm_data:
        if _comm.change_type:
            if _task_comm.get(_comm.delay) is None:
                _task_comm.__setitem__(_comm.delay, [])
            _task_comm[_comm.delay].append(_comm)
        else:
            comm_data.append(_comm)
        if _comm.change_type == '-':
            comm_data.append(_comm)

    static_schedule(exp_id, pods_data=pods_data, pod2idx=pod2idx, nodes_data=nodes_data, comm_data=comm_data)

    logger.info(f'finish static schedule')

    logger.info(f'task comm size:{_task_comm.__len__()}')

    for _delay in _task_comm.keys():
        # delay 为延迟一分钟数据
        scheduler.enter(_delay * 60, 1, enter_dynamic_task, argument=(
            _delay, _nodes_resources_excel, _pod2idx, _task_comm, _task_pods, comm_data, exp_id, nodes_data,
            pod2idx, pods_data))
        scheduler.run()

    logger.info(f'finish affinity schedule,exp_id:{exp_id}')


def enter_dynamic_task(_delay, _nodes_resources_excel, _pod2idx, _task_comm, _task_pods, comm_data, exp_id, nodes_data,
                       pod2idx, pods_data):
    if STOPED_EXP.get(exp_id):
        logger.warning(f'terminated exp:{exp_id},stopping operate schedule')
        return
    logger.info(f'start dynamic schedule')
    # 智能体列表增加变化智能体（不能删除，亲和性评分会乱）
    for _pod in _task_pods.get(_delay):
        if _pod.change_type == '+':
            pods_data.append(_pod)
            pod2idx.__setitem__(_pod.name, _pod2idx.get(_pod.name))
    # 拷贝静态通信关系
    _this_comm = comm_data
    for _comm in _task_comm.get(_delay):
        # 增加新增的通信关系
        if _comm.change_type == '+':
            _this_comm.append(_comm)
        # 删除取消的通信关系
        if _comm.change_type == '-':
            _this_comm.remove(_comm)
    _node_resource = load_node_resource(_nodes_resources_excel)
    dynamic_schedule(exp_id, pods_data=pods_data, pod2idx=pod2idx, nodes_data=nodes_data, comm_data=_this_comm,
                     new_pods=_task_pods.get(_delay),
                     node_resource=_node_resource)
    logger.info(f'finish dynamic schedule')
