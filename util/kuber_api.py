import os
from dateutil import parser
from kubernetes import client, config, watch

from util.logger import logger
from util.the_os import package_path

_config_path = os.path.join(package_path(), "kube_config.yaml")
print(_config_path)
config.load_kube_config(config_file=_config_path)
# 初始化API客户端
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()


def deploy_from_yaml_str(yaml_docs):
    #
    # for doc in yaml_docs:
    #     if not doc:
    #         continue
    #
    #     try:
    #         resource_name = doc["metadata"]["name"]
    #
    #         # 根据资源类型调用对应的API
    #         if doc["kind"] == "Deployment":
    #             # 先尝试创建，如果已存在则更新
    #             try:
    #                 resp = apps_v1.create_namespaced_deployment(
    #                     namespace="default",
    #                     body=doc
    #                 )
    #                 # logger.info(f"Deployment {resource_name} created,got response {resp}")
    #                 logger.info(f"Deployment {resource_name} created")
    #             except client.exceptions.ApiException as create_err:
    #                 if create_err.status == 409:  # 已存在
    #                     resp = apps_v1.replace_namespaced_deployment(
    #                         name=resource_name,  # 添加name参数
    #                         namespace="default",
    #                         body=doc
    #                     )
    #                     # logger.info(f"Deployment {resource_name} updated,got response {resp}")
    #                     logger.info(f"Deployment {resource_name} created")
    #                 else:
    #                     raise
    #
    #         elif doc["kind"] == "Service":
    #             # 同样的逻辑处理Service
    #             try:
    #                 resp = core_v1.create_namespaced_service(
    #                     namespace="default",
    #                     body=doc
    #                 )
    #                 # logger.info(f"Service {resource_name} created,got response {resp}")
    #                 logger.info(f"Service {resource_name} created")
    #             except client.exceptions.ApiException as create_err:
    #                 if create_err.status == 409:
    #                     resp = core_v1.replace_namespaced_service(
    #                         name=resource_name,
    #                         namespace="default",
    #                         body=doc
    #                     )
    #                     # logger.info(f"Service {resource_name} updated,got response {resp}")
    #                     logger.info(f"Service {resource_name} updated")
    #                 else:
    #                     raise
    #
    #         else:
    #             logger.warning(f"Unsupported resource type: {doc['kind']}")
    #
    #     except Exception as e:
    #         logger.error(
    #             f"Error processing {doc.get('kind', 'unknown')} {doc.get('metadata', {}).get('name', 'unnamed')}: {str(e)}")
    #         # 可以选择继续处理下一个资源或直接raise
    pass
