from typing import Dict

import pandas as pd
import argparse
import logging

from affinity.models import SingleSchedulerPlan, Communication, BasePod
from util.logger import logger


class Agent:
    def __init__(self, name: str, cpus: int, memory: int, gpus: int, disk: int) -> None:
        self.name = name
        self.cpus = cpus
        self.memory = memory
        self.gpus = gpus
        self.disk = disk
        self.target = ""
        self.frequency = 1.0
        self.package = 1
        self.amount = 1
        self.node = ""


def read_excel_and_construct_agents(pods_data: list[BasePod], plan: list[SingleSchedulerPlan]) -> Dict[str, Agent]:
    agents_dict = {}

    # 读取资源信息
    try:
        for _pod in pods_data:
            name = _pod.name  # 第一列是名称
            cpus = _pod.cpu if _pod.cpu else 0
            memory = _pod.mem if _pod.mem else 0
            gpus = _pod.gpu if _pod.gpu else 0
            disk = _pod.disk if _pod.disk else 0

            agents_dict[name] = Agent(name, cpus, memory, gpus, disk)
    except Exception as e:
        logger.error(f"读取资源数据失败: {str(e)}")
        raise
    # 读取节点信息
    try:
        for _plan in plan:
            name = _plan.pod  # 第一列是Agent名称
            node = _plan.scheduled_node  # 第二列是节点名称

            if name not in agents_dict:
                logger.error(f'Agent {name} 不存在于资源文件中!')
                continue

            agents_dict[name].node = node
    except Exception as e:
        logger.error(f"读取节点数据失败: {str(e)}")
        raise

    return agents_dict


def read_excel_and_generate_yamls(agents: Dict[str, Agent],
                                  comm_data: list[Communication]) -> list[str]:
    generated = set()

    try:
        for _comm in comm_data:
            target = _comm.tgt_pod
            source = _comm.src_pod
            frequency = _comm.freq if _comm.freq else 0.0
            package = _comm.package if _comm.package else 0
            amount = _comm.count if _comm.count else 0

            # 检查参数合法性
            if frequency == 0 or package == 0 or amount == 0:
                logger.warning(
                    f'参数不合法: frequency: {frequency}, package: {package}, amount: {amount}!')
                continue

            # 处理重复源
            if source in generated:
                if 'command' in source and 'equipt' in target:
                    source, target = target, source  # 交换源和目标
                else:
                    logger.warning(f'{source} 已被使用过!')
                    continue

            # 检查Agent是否存在
            if source not in agents or target not in agents:
                logger.warning(f'{source} 或 {target} 未在资源配置文件中定义!')
                continue

            # 更新Agent信息
            agents[source].target = target
            agents[source].frequency = frequency
            agents[source].package = package
            agents[source].amount = amount
            generated.add(source)

        # 生成YAML文件
        return generate(agents)

    except Exception as e:
        logger.error(f"读取通信数据失败: {str(e)}")
        raise


def generate(agents: dict[str, Agent]) -> list[str]:
    deploy = []
    for agent in agents.values():
        deploy.append(
            generate_yamls(agent.name.replace('_', '-'), agent.cpus, agent.memory, agent.frequency, agent.package,
                           agent.target.replace('_', '-'), agent.amount, agent.node))
    return deploy


def generate_yamls(name: str, cpu: int, memory: int, frequency: float, package: int, target: str, amount: int,
                   node: str) -> str:
    return f"""
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  labels:
    app: {name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      name: {name}
      labels:
        app: {name}
    spec:
      nodeSelector:
        agent: {node}
      containers:
        - name: {name}
          image: registry.cn-hangzhou.aliyuncs.com/lexmargin/agent:v0.5
          command: ["python3", "/agent/main.py", "-c", "{cpu}", "-m", "{memory}", "-f", "{frequency}", "-p", "{package}", "-t", "{target}", "-a", "{amount}"]
          ports:
          - containerPort: 11111
          - containerPort: 11112
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    app: agents
spec:
  selector:
    app: {name}
  ports:
    - protocol: TCP
      port: 11111  # 对外提供服务的端口，可以根据实际需求修改
      targetPort: 11111  # Pod 内实际监听的端口，要和 Pod 中应用监听的端口对应
      name: server
    - protocol: TCP
      port: 11112  # 对外提供服务的端口，可以根据实际需求修改
      targetPort: 11112  # Pod 内实际监听的端口，要和 Pod 中应用监听的端口对应
      name: metrics
  type: ClusterIP  # 服务类型，这里使用 ClusterIP，可根据需求换成其他类型（如 NodePort、LoadBalancer 等）""".format(name,
                                                                                                               cpu,
                                                                                                               memory,
                                                                                                               frequency,
                                                                                                               package,
                                                                                                               target,
                                                                                                               amount)


