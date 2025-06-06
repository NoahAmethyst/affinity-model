from io import BytesIO

import pandas as pd

from affinity.calculate import Graph, load_pods, load_nodes, load_comm
from affinity.dynamic_schedule import dynamic_schedule, load_node_resource
from affinity.models import SingleSchedulerPlan
from affinity.multi_stage_scheduler import MultiStageScheduler, static_schedule
from affinity.parse_schedule import read_excel_and_construct_agents, read_excel_and_generate_yamls
from util.logger import logger


def exec_schedule(exp_id: int, contents):
    logger.info(f'start static schedule')

    file_obj = BytesIO(contents)
    _comm_excel = pd.read_excel(io=file_obj,
                                sheet_name='d-communication')
    _nodes_resources_excel = pd.read_excel(io=file_obj,
                                           sheet_name='d-node_resource')

    _nodes_excel = pd.read_excel(io=file_obj,
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel(io=file_obj,
                                sheet_name='pods')

    pods_data, pod2idx = load_pods(pods_excel=_pods_excel)

    nodes_data = load_nodes(nodes_excel=_nodes_excel)

    comm_data = load_comm(comm_excel=_comm_excel)

    static_schedule(exp_id, pods_data=pods_data, pod2idx=pod2idx, nodes_data=nodes_data, comm_data=comm_data)
    logger.info(f'finish static schedule')

    _tasks_excel = pd.read_excel(io=file_obj,
                                 sheet_name='d-agents')

    _new_pods_excel = pd.concat([_pods_excel, _tasks_excel], ignore_index=True)

    _new_pods,_ = load_pods(pods_excel=_tasks_excel)

    logger.info(f'start dynamic schedule')

    _node_resource = load_node_resource(_nodes_resources_excel)

    dynamic_schedule(exp_id, pods_data=pods_data, pod2idx=pod2idx, nodes_data=nodes_data, comm_data=comm_data,
                     new_pods=_new_pods,
                     node_resource=_node_resource)
    logger.info(f'finish dynamic schedule')
