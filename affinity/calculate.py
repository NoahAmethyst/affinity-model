import json
import os
from enum import Enum
from operator import contains
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import pytest
from pandas import ExcelFile

from affinity.models import BasePod, Communication, BaseNode


class Graph:
    net_affinity_name = 'net_affinity'  # 网络亲和性标签
    data_name = 'data'  # 原始输入数据标签
    command_affinity_name = 'command_affinity'  # 指挥亲和性标签
    race_affinity_name = 'race_affinity'  # 资源竞争亲和性标签
    weight = [1000, 1, 0]
    attr = [net_affinity_name, race_affinity_name]

    def __init__(self, pods_data: list[BasePod], pod2idx: dict[str, int], comm_data: list[Communication],
                 nodes_data: list[BaseNode]):
        self.pod_graph = nx.Graph()
        self.command_graph = nx.Graph()
        ### read pods

        self.pods = pods_data
        self.pod2idx = pod2idx

        for _pod in pods_data:
            self.pod_graph.add_node(_pod)

        ### read communication
        for comm in comm_data:
            _src = None
            _tgt = None

            for _pod in self.pods:
                if comm.src_pod == _pod.name:
                    _src = _pod
                if comm.tgt_pod == _pod.name:
                    _tgt = _pod
            if _src is None or _tgt is None:
                continue
            self.pod_graph.add_edge(_src, _tgt,
                                    data=comm, kind="comm")
            self.pod_graph.add_edge(_src, _tgt,
                                    label=comm.to_string())

        ### read nodes

        self.nodes = nodes_data

    def net_affinity(self):
        """ 计算网络的亲和性 """
        for u, v in self.pod_graph.edges:
            d = self.pod_graph.get_edge_data(u, v)[Graph.data_name]
            self.pod_graph.add_edge(u, v, net_affinity=d.freq * d.package)

    def command_affinity(self):
        """ 指挥交互关系亲和性 """
        for x in self.pod_graph.nodes:
            for y in self.pod_graph.nodes:
                if x == y:
                    break
                x_platform = self.name2platform[x.platform]
                y_platform = self.name2platform[y.platform]
                length = nx.shortest_path_length(self.command_graph, x_platform, y_platform)
                if length == 0:
                    length = 0.1
                self.pod_graph.add_edge(x, y, command_affinity=1 / length)

    def race_affinity(self):
        """ 资源竞争亲和性 """
        for source in self.pod_graph.nodes:
            for target in self.pod_graph.nodes:
                if source == target:
                    break
                v = BasePod.race_affinity(source, target)
                self.pod_graph.add_edge(source, target, race_affinity=-v)

    # 计算节点亲和性（资源竞争，是否 > pod 需要，如果 > 就是1）
    def node_affinity(self):
        matrix = np.zeros((self.pod_graph.number_of_nodes(), len(self.nodes)), dtype=int)
        for pod in self.pod_graph.nodes:
            # x = self.pod2idx[pod.name]
            x = 0
            for _pod in self.pods:
                if pod.name == _pod.name:
                    break
                x += 1
            for y, node in enumerate(self.nodes):
                if node >= pod:
                    matrix[x, y] = 1
                else:
                    matrix[x, y] = 0
        return matrix

    def pod_affinity_to_matrix(self, attr: [str], weight: [float], norm=True):
        matrixs = [np.zeros((self.pod_graph.number_of_nodes(), self.pod_graph.number_of_nodes()), dtype=float) for i in
                   range(len(attr))]
        for u, v, d in self.pod_graph.edges(data=True):
            # i = self.pod2idx[u.name]
            # j = self.pod2idx[v.name]
            i = 0
            j = 0
            _index = 0
            for _pod in self.pods:
                if _pod.name == u.name:
                    i = _index
                if _pod.name == v.name:
                    j = _index
                _index += 1
            for t, a in enumerate(attr):
                if d.__contains__(a):
                    matrixs[t][i][j] = d[a]
                    matrixs[t][j][i] = d[a]
        if norm:
            for i, matrix in enumerate(matrixs):
                matrixs[i] = (matrix - matrix.min()) / (matrix.max() - matrix.min())
        result = np.zeros((self.pod_graph.number_of_nodes(), self.pod_graph.number_of_nodes()), dtype=float)
        for w, m in zip(weight, matrixs):
            result += w * m
        if norm:
            result = (result - result.min()) / (result.max() - result.min())
        return result

    def cal_affinity(self):
        # ### 计算保存pod间亲和性
        self.net_affinity()
        # g.command_affinity()
        self.race_affinity()
        pod_affinity = self.pod_affinity_to_matrix(Graph.attr, Graph.weight)
        node_affinity = self.node_affinity()
        return pod_affinity, node_affinity


def load_pods(pods_excel):
    pods: list[BasePod] = []
    pod2idx: dict[str, int] = {}
    for idx, row in pods_excel.iterrows():
        pod = BasePod.from_dataframe(row)
        pods.append(pod)
        pod2idx[pod.name] = idx
    return pods, pod2idx


def load_comm(comm_excel):
    comm: list[Communication] = []
    for _, row in comm_excel.iterrows():
        comm.append(Communication.from_dataframe(row))
    return comm


def load_nodes(nodes_excel) -> list[BaseNode]:
    nodes: list[BaseNode] = []
    for _, row in nodes_excel.iterrows():
        node = BaseNode.from_dataframe(row)
        nodes.append(node)
    return nodes
