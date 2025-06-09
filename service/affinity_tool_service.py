import http.client
import json
import logging
import os
from typing import Optional

import numpy as np

from affinity.models import SingleSchedulerPlan, Communication
from service.models.affinity_tool_models import EventType, ExperimentData, NodeAgentsInfo, InteractionDetail, \
    AffinityValue
from util.constant import AFFINITY_SERVER, AFFINITY_PORT
from util.logger import logger
from util.time_util import now_millis

_host = os.getenv(AFFINITY_SERVER)
_port = os.getenv(AFFINITY_PORT)
affinity_cli = http.client.HTTPConnection(_host, int(_port))


def report_event(exp_id: int, _type: EventType, message: Optional[str] = None,
                 duration: Optional[int] = None):
    try:
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
        logger.info(f'report event:{EventType.get_description(_type.value)} to server {_host}:{_port}')
        affinity_cli.request("POST", "/api/affinity_tools/exp/loggers/create", payload, headers)
        res = affinity_cli.getresponse()
        res.read()
        logger.info(f'report event,get response:{res.status}')
    except Exception as e:
        logging.error(f'report event to server{_host}:{_port} failed:{e}')


def build_exp_data(exp_id: int, plans: list[SingleSchedulerPlan], comm_data: list[Communication],
                   pod_affinity: np.ndarray, pod2idx: dict[str, int]):
    agents_node_info = NodeAgentsInfo.load(plans)

    interaction_details = InteractionDetail.load(comm_data)

    agents_affinity = AffinityValue.load(pod_affinity, pod2idx)

    return ExperimentData(
        exp_id=exp_id,
        node_agents_info=agents_node_info,
        interaction_detail=interaction_details,
        affinity_values=agents_affinity,
        gather_at=now_millis(),
    )


def sync_agents_graph(exp_data: ExperimentData):
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
        res.read()
        logger.info(f'sync agents graph data,get response:{res.status}')
    except Exception as e:
        logging.error(f'report event to server{_host}:{_port} failed:{e}')
