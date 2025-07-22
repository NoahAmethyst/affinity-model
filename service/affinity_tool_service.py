import http.client
import json
import logging
import os
from typing import Optional

import numpy as np

from affinity.models import SingleSchedulerPlan, Communication
from service.models.affinity_tool_models import EventType, ExperimentData, NodeAgentsInfo, InteractionDetail, \
    AffinityValue
from util.constant import AFFINITY_SERVER, AFFINITY_PORT, REPORT_EVENT
from util.kuber_api import label_with_nodes
from util.logger import logger
from util.time_util import now_millis

_host = os.getenv(AFFINITY_SERVER)
_port = os.getenv(AFFINITY_PORT)
affinity_cli = http.client.HTTPConnection(_host, int(_port))
CURR_EXP_ID = 0


def report_event(exp_id: int, _type: EventType, message: Optional[str] = None,
                 duration: Optional[int] = None):
    CURR_EXP_ID = exp_id
    s = int(os.getenv(REPORT_EVENT))
    if int(os.getenv(REPORT_EVENT)) == 0:
        return
    try:
        payload = json.dumps({
            "exp_id": exp_id,
            "type": _type,
            "message": message,
            "trigger_at": now_millis() // 1000,
            "duration": duration
        })
        headers = {
            'Content-Type': 'application/json'
        }
        logger.info(f'report event:{EventType.get_description(_type.value)} to server {_host}:{_port}')
        affinity_cli.request("POST", "/api/affinity_tools/exp/loggers/create", payload, headers)
        res = affinity_cli.getresponse()
        res.read()
        logger.info(f'report event,get response:{res.status}')
    except Exception as e:
        logging.error(f'report event to server{_host}:{_port} failed:{e}')


def build_exp_data(exp_id: int, plans: list[SingleSchedulerPlan], comm_data: list[Communication],
                   pod_affinity: np.ndarray, pods):
    agents_node_info = NodeAgentsInfo.load(plans)

    interaction_details = InteractionDetail.load(comm_data)

    agents_affinity = AffinityValue.load(pod_affinity, pods)

    return ExperimentData(
        exp_id=exp_id,
        node_agents_info=agents_node_info,
        interaction_detail=interaction_details,
        affinity_values=agents_affinity,
        gather_at=now_millis() // 1000,
    )


def sync_agents_graph(exp_data: ExperimentData):
    if int(os.getenv(REPORT_EVENT)) == 0:
        return
    try:
        logger.info(f'sync agents graph data,exp_id:{exp_data.exp_id}')
        headers = {
            'Content-Type': 'application/json'
        }
        # Serialize the ExperimentData object to JSON string
        json_data = json.dumps(exp_data, default=lambda o: o.__dict__)
        affinity_cli.request(method="POST", url="/api/affinity_tools/sim_exp/node/agents/graph/create", body=json_data,
                             headers=headers)
        res = affinity_cli.getresponse()
        response_body = res.read().decode('utf-8')
        logger.info(f'sync agents graph data,get response:{response_body}')
    except Exception as e:
        logging.error(f'report event to server{_host}:{_port} failed:{e}')


def report_plan(exp_id: int, exp_type: str, exp_plan: list[SingleSchedulerPlan]):
    logger.info('report plan')
    try:
        payload = {
            "exp_id": exp_id,
            "exp_type": exp_type,
            "data": [
                {
                    "agent": plan.pod,
                    "node": label_with_nodes.get(plan.scheduled_node)
                }
                for plan in exp_plan
            ]
        }

        # 转换为 JSON 字符串
        payload_json = json.dumps(payload)
        headers = {
            'Content-Type': 'application/json'
        }
        affinity_cli.request("POST", "/api/affinity_tools/sim_exp/deploy_scheme/create", payload_json, headers)
        res = affinity_cli.getresponse()
        data = res.read()
        logger.info(f'report plan,get response:{data}')
    except Exception as e:
        logging.error(f'report event to server{_host}:{_port} failed:{e}')
