import yaml

from util.kuber_api import deploy_from_yaml_str, create_namespace, delete_all_deployments_in_namespace, \
    delete_all_services
from util.logger import logger

EXP_NAMESPACE = 'affinity-exp'

STOPED_EXP: dict[int, bool] = {}
MONITORING_EXP: dict[int, bool] = {}


def operate_schedule(exp_id: int, deploys: list[str]):
    _namespace = f'{EXP_NAMESPACE}-{exp_id}'
    _namespace_ = create_namespace(_namespace)
    if _namespace_ is None:
        _namespace = 'default'

    # deploy service-monitor
    if not MONITORING_EXP.get(exp_id):
        # create_service_monitor(_namespace_,exp_id)
        MONITORING_EXP.__setitem__(exp_id, True)
    logger.info(f'Creating service for {_namespace}')
    for _deploy in deploys:
        yaml_docs = yaml.safe_load_all(_deploy)
        deploy_from_yaml_str(yaml_docs, _namespace)


def terminate_schedule(exp_id: int):
    logger.info(f'terminating affinity exp:{exp_id}')
    _namespace = f'{EXP_NAMESPACE}-{exp_id}'
    delete_all_deployments_in_namespace(_namespace)
    delete_all_services(_namespace)
    STOPED_EXP.__setitem__(exp_id, True)
