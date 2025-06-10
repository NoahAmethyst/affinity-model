import os
from typing import Optional

from kubernetes import client, config

from util.logger import logger
from util.the_os import package_path

_config_path = os.path.join(package_path(), "kube_config.yaml")
print(_config_path)
config.load_kube_config(config_file=_config_path)
# 初始化API客户端
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
custom_api = client.CustomObjectsApi()

nodes_with_label: dict[str, str] = {}


def init_nodes_with_label(label_value: str):
    label = 'agent'
    if nodes_with_label.get(label_value) is None:
        node_names = fetch_node_with_label(label, label_value)
        for node_name in node_names:
            nodes_with_label.__setitem__(label_value, node_name)
        logger.info(f'init nodes name :{nodes_with_label}')


def fetch_node_with_label(label: str, label_value: str) -> list[str]:
    # 根据 Label 获取 Node
    label_selector = f"{label}={label_value}"
    _nodes = core_v1.list_node(label_selector=label_selector)

    nodes: list[str] = []
    # 输出 Node 名称
    for node in _nodes.items:
        nodes.append(node.metadata.name)
    return nodes


def deploy_from_yaml_str(yaml_docs, namespace: Optional[str]):
    for doc in yaml_docs:
        if not doc:
            continue
        try:
            resource_name = doc["metadata"]["name"]

            # 根据资源类型调用对应的API
            if doc["kind"] == "Deployment":
                # 先尝试创建，如果已存在则更新
                try:
                    resp = apps_v1.create_namespaced_deployment(
                        namespace=namespace,
                        body=doc
                    )
                    # logger.info(f"Deployment {resource_name} created,got response {resp}")
                    logger.info(f"Deployment {resource_name} created")
                except client.exceptions.ApiException as create_err:
                    if create_err.status == 409:  # 已存在
                        resp = apps_v1.replace_namespaced_deployment(
                            name=resource_name,  # 添加name参数
                            namespace=namespace,
                            body=doc
                        )
                        # logger.info(f"Deployment {resource_name} updated,got response {resp}")
                        logger.info(f"Deployment {resource_name} created")
                    else:
                        raise

            elif doc["kind"] == "Service":
                # 同样的逻辑处理Service
                try:
                    resp = core_v1.create_namespaced_service(
                        namespace=namespace,
                        body=doc
                    )
                    # logger.info(f"Service {resource_name} created,got response {resp}")
                    logger.info(f"Service {resource_name} created")
                except client.exceptions.ApiException as create_err:
                    if create_err.status == 409:
                        resp = core_v1.replace_namespaced_service(
                            name=resource_name,
                            namespace=namespace,
                            body=doc
                        )
                        # logger.info(f"Service {resource_name} updated,got response {resp}")
                        logger.info(f"Service {resource_name} updated")
                    else:
                        raise
            elif doc["kind"] == "ServiceMonitor":
                # ServiceMonitor的CRD信息
                group = "monitoring.coreos.com"
                version = "v1"
                plural = "service-monitors"

                # 检查ServiceMonitor是否已存在
                try:
                    # 如果不存在，则创建
                    response = custom_api.create_namespaced_custom_object(
                        group=group,
                        version=version,
                        namespace=namespace,
                        plural=plural,
                        body=doc
                    )
                    logger.info(f"ServiceMonitor {resource_name} created")


                except client.exceptions.ApiException as e:
                    if e.status == 409:
                        # 如果存在，则更新
                        response = custom_api.replace_namespaced_custom_object(
                            group=group,
                            version=version,
                            namespace=namespace,
                            plural=plural,
                            name=resource_name,
                            body=doc
                        )
                        logger.info(f"ServiceMonitor {resource_name} updated")
                    else:
                        raise

            else:
                logger.warning(f"Unsupported resource type: {doc['kind']}")

        except Exception as e:
            logger.error(
                f"Error processing {doc.get('kind', 'unknown')} {doc.get('metadata', {}).get('name', 'unnamed')}: {str(e)}")
            # 可以选择继续处理下一个资源或直接raise
            raise


def create_namespace(_namespace: str) -> str | None:
    return_namespace = None
    try:
        # 定义命名空间对象
        namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=_namespace)
        )

        # 创建命名空间
        core_v1.create_namespace(body=namespace)

        logger.info(f"Create namespace '{_namespace}' success!")
        return_namespace = _namespace
    except client.exceptions.ApiException as e:
        if e.status == 409:
            logger.info(f"namespace '{_namespace}' exist")
            return_namespace = _namespace
        else:
            logger.error(f"create namespace {_namespace} failed: {e}")
    except Exception as e:
        logger.error(f"create namespace {_namespace} failed: {e}")
    return return_namespace


def delete_all_deployments_in_namespace(namespace):
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace)

        if not deployments.items:
            logger.warning(f"namespace {namespace} has no Deployments")
            return

        # 删除每个Deployment
        for deployment in deployments.items:
            try:
                apps_v1.delete_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=namespace,
                    body=client.V1DeleteOptions()
                )
                logger.info(f"delete Deployment: {deployment.metadata.name}")
            except client.exceptions.ApiException as e:
                logger.error(f"delete Deployment {deployment.metadata.name} failed: {e}")

        logger.info(f"delete all deployments from namespace {namespace} ")

    except Exception as e:
        logger.error(f"delete all deployments from namespace {namespace} failed: {e}")


def create_service_monitor(namespace: str):
    # 修正后的 ServiceMonitor 定义
    service_monitor = {
        "apiVersion": "monitoring.coreos.com/v1",
        "kind": "ServiceMonitor",
        "metadata": {
            "name": "agent-service-monitor",  # 注意名称不要有下划线
            "namespace": namespace,  # 添加这一行
            "labels": {
                "release": "monitor"
            }
        },
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": "agents"
                }
            },
            "endpoints": [
                {
                    "port": "metrics",
                    "path": "/metrics",
                    "interval": "10s",
                    "scheme": "http"  # 修正拼写错误
                }
            ],
            "namespaceSelector": {
                "matchNames": [namespace]
            }
        }
    }

    try:
        custom_api.create_namespaced_custom_object(
            group="monitoring.coreos.com",
            version="v1",
            namespace=namespace,
            plural="servicemonitors",  # 注意复数形式可能是 servicemonitors 而不是 service-monitors
            body=service_monitor
        )
        print("ServiceMonitor created successfully")
    except client.exceptions.ApiException as e:
        print(f"Exception when creating ServiceMonitor: {e}")
        print(f"Full error details: {e.body}")


def test_create_service_monitor():
    create_service_monitor('affinity-exp-1')


def test_fetch_node():
    label = 'agent'
    value = 'node-1'
    node_names = fetch_node_with_label(label, value)
    for _node_name in node_names:
        print(_node_name)
