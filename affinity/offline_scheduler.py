# 静态调度框架
import os
import random
from random import shuffle
from typing import Any
import numpy as np
import pandas as pd
import yaml
from affinity.models import BasePod, BaseNode, BaseObject, SingleSchedulerPlan
from util.logger import init_logger, logger

init_logger()


class Scheduler:
    affinity_weight = 1
    avg_usage_weight = 1
    var_usage_weight = 1

    def __init__(self, pods_data, nodes_data, pod_affinity, node_affinity):
        self.pods: [BasePod] = []
        self.nodes: [BaseNode] = []
        self.pod_affinity = pod_affinity
        self.node_affinity = node_affinity
        self.read_input(pods_data=pods_data, nodes_data=nodes_data, pods_affinity=pod_affinity,
                        nodes_affinity=node_affinity)

        self.scheduler_name = ""

    def schedule(self) -> [int]:
        raise NotImplementedError

    def affinity(self, plan: [int]) -> int:
        """ 计算节点直接亲和性 """
        res = 0
        affinity_pod = self.pod_affinity
        ### calc affinity between pods
        for pod1_idx in range(len(self.pods)):
            for pod2_idx in range(pod1_idx + 1, len(self.pods)):
                # affinity
                if plan[pod1_idx] == plan[pod2_idx]:
                    res += affinity_pod[pod1_idx, pod2_idx]
                if plan[pod1_idx] != plan[pod2_idx]:
                    res -= affinity_pod[pod1_idx, pod2_idx]
        return res

    def calc_cost(self, plan: [int]) -> float:
        min_usage, max_usage, usage = self.usage(plan)

        affinity_cost = self.affinity(plan)
        avg_usage_cost = np.average(max_usage)
        var_usage_cost = np.var(max_usage)
        logger.info(f'affinity: {affinity_cost}, avg: {avg_usage_cost}, var: {var_usage_cost}')
        return -(var_usage_cost * self.var_usage_weight +
                 affinity_cost * self.affinity_weight +
                 avg_usage_cost * self.avg_usage_weight)

    def usage(self, plan: np.ndarray) -> ([float], [float], [BaseObject]):
        """输出每个节点的 资源最低利用率 最高利用率 和 每个资源的利用率"""
        occupied = [None for _ in range(len(self.nodes))]
        for pod_idx, node_idx in enumerate(plan):
            # Add bounds checking
            if node_idx >= len(occupied):
                logger.error(f"Invalid node index {node_idx} in plan")
                continue

            if occupied[node_idx] is not None:
                tmp = occupied[node_idx]
            else:
                tmp = BaseObject("", 0, 0, 0, 0)
            tmp += self.pods[pod_idx]
            occupied[node_idx] = tmp

        min_usage = [0 for _ in range(len(occupied))]
        max_usage = [0 for _ in range(len(occupied))]
        usage = [BaseObject("", 0, 0, 0, 0) for _ in range(len(occupied))]
        for node_idx, u in enumerate(occupied):
            if u is None:
                min_usage[node_idx] = 0
                continue
            min_usage[node_idx] = self.nodes[node_idx].min_usage(u)
            max_usage[node_idx] = self.nodes[node_idx].max_usage(u)
            usage[node_idx] = self.nodes[node_idx].usage(u)
        return min_usage, max_usage, usage

    def used(self, plan: np.ndarray) -> [BaseObject]:
        """Calculate resource usage for each node with bounds checking"""
        # Initialize with empty BaseObjects
        used = [BaseObject() for _ in range(len(self.nodes))]

        for pod_idx, node_idx in enumerate(plan):
            # Validate node index before accessing
            if node_idx >= len(used):
                logger.error(f"Invalid node index {node_idx} in plan")
                continue

            # Update resource usage
            used[node_idx] += self.pods[pod_idx]

        return used

    def read_pod_yamls(self, pods_dir: str) -> dict[str, Any]:
        entries = os.listdir(pods_dir)
        pods = {}
        for entry in entries:
            with open(os.path.join(pods_dir, entry), 'r') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
                pods[data['metadata']['name']] = data
        self.pod_yaml = pods
        return pods

    def save_pod_yamls(self, dir: str):
        if self.plan is None:
            logger.info('call schedule first')
            return
        pod_yaml = self.pod_yaml
        plan = self.plan

        for pod_name, pod_idx in self.podName2idx.items():
            with open(os.path.join(dir, pod_name + '.yaml'), 'w') as file:
                one_yaml = pod_yaml[self.podIdx2name[pod_idx]]
                one_yaml['metadata']['nodeName'] = self.nodeIdx2name[plan[pod_idx]]
                yaml.dump(one_yaml, file, default_flow_style=False)

    def read_input(self, pods_data: list[BasePod], nodes_data: list[BaseNode], pods_affinity, nodes_affinity):
        """ 读取输入数据 """
        ### read pods
        _podName2idx = {}
        _index = 0
        for _pod in pods_data:
            _podName2idx.__setitem__(_pod.name, _index)
            _index += 1
        self.podName2idx = _podName2idx
        self.pods = pods_data

        _index = 0

        _node2idx = {}
        for _node in nodes_data:
            _node2idx.setdefault(_node.name, _index)
            _index += 1

        self.nodeName2idx = _node2idx
        self.nodes = nodes_data

        self.pod_affinity = pods_affinity
        self.node_affinity = nodes_affinity
        ### shuffle
        self.shuffle()

    def shuffle(self):
        """ 将输入的pod顺序打乱 """
        index = list(range(len(self.pods)))  # index[i]表示原位置
        random.seed(42)
        shuffle(index)
        pods = [self.pods[i] for i in index]
        ### 转换pod affinity
        pod_affinity = np.copy(self.pod_affinity)
        for i in range(pod_affinity.shape[0]):
            for j in range(pod_affinity.shape[1]):
                pod_affinity[i, j] = self.pod_affinity[index[i], index[j]]
        ### 转换node affinity
        node_affinity = np.copy(self.node_affinity)
        for i in range(node_affinity.shape[0]):
            node_affinity[i, :] = self.node_affinity[index[i], :]

        self.pods = pods
        self.pod_affinity = pod_affinity
        self.node_affinity = node_affinity

    def get_node_num(self):
        return len(self.nodes)

    def get_pod_num(self):
        return len(self.pods)

    def check(self, plan: np.ndarray) -> bool:
        """ 检查放置方案是否合法 """
        used = self.used(plan)
        for u, node in zip(used, self.nodes):
            tmp = node - u

            if tmp.mem < 0 or tmp.disk < 0 or tmp.gpu < 0:
                return False
        return True

    def save_plan(self, save_path: str, plan: []):
        """保存调度结果"""
        # Validate plan length matches pods
        if len(plan) != len(self.pods):
            logger.error(f"Plan length {len(plan)} doesn't match pod count {len(self.pods)}")
            return

        # Validate all node indices
        valid_entries = []
        for pod_idx, node_idx in enumerate(plan):
            if node_idx >= len(self.nodes):
                logger.error(f"Invalid node index {node_idx} for pod {self.pods[pod_idx].name}")
                continue
            valid_entries.append([self.pods[pod_idx].name, self.nodes[node_idx].name])

        # Only save if all entries are valid
        if len(valid_entries) == len(self.pods):
            df = pd.DataFrame(valid_entries, columns=["name", "node"])
            df.to_csv(os.path.join(save_path, f'{self.scheduler_name}.csv'), index=False)
        else:
            logger.error("Plan contains invalid node assignments - not saving")

    @classmethod
    def check_and_output(cls, scheduler, save_path: str, plan: [int]):
        ### check
        result = scheduler.check(plan)
        if not result:
            logger.info('check failed')
            return

        ### 计算cost
        cost = scheduler.calc_cost(plan)
        logger.info(f'cost: {cost}')

        ### 计算利用率
        min_usage, max_usage, usage = scheduler.usage(plan)
        for i, v in enumerate(zip(min_usage, max_usage, usage)):
            min_u, max_u, u = v
            logger.info(f'node({i}): min_usage:{min_u}, max_usage:{max_u}, usage:[{u.to_string()}]')

        ### 保存结果
        scheduler.save_plan(save_path, plan)

    def check_and_gen(self, scheduler, plan: [int]) -> list[SingleSchedulerPlan] | None:
        """Validate a scheduling plan and generate execution details."""
        # Early return if plan is invalid
        # if not scheduler.check(plan):
        #     logger.warn('Plan validation failed')
        #     return None

        # Validate all node indices in plan
        for node_idx in plan:
            if node_idx >= len(self.nodes):
                logger.error(f"Invalid node index {node_idx} in plan")
                return None

        # Log cost information
        cost = scheduler.calc_cost(plan)
        logger.info(f'Total cost: {cost}')

        # Generate plan objects with validation
        return [
            SingleSchedulerPlan(self.pods[pod].name, self.nodes[node].name)
            for pod, node in enumerate(plan)
            if node < len(self.nodes)  # Additional safety check
        ]
