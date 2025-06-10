import pandas as pd

from affinity.calculate import Graph, load_pods, load_nodes, load_comm
from affinity.models import Communication, BasePod
from affinity.multi_stage_scheduler import MultiStageScheduler
from affinity.parse_schedule import read_excel_and_construct_agents, read_excel_and_generate_yamls
from service.models.affinity_tool_models import NodeAgentsInfo, InteractionDetail, AffinityValue
from util.kuber_api import init_nodes_with_label


def test_calculate_affinity():
    _comm_excel = pd.read_excel(io='/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='communication')
    _nodes_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='pods')

    pods_data, pods2idx = load_pods(_pods_excel)
    nodes_data = load_nodes(_nodes_excel)
    comm_data = load_comm(_comm_excel)

    g = Graph(pods_data=pods_data, pod2idx=pods2idx, comm_data=comm_data, nodes_data=nodes_data)
    pod_affinity, node_affinity = g.cal_affinity()
    print(f'pods affinity:\n{pod_affinity=}')
    print(f'nodes affinity:\n{node_affinity=}')


def test_generate_plan():
    _comm_excel = pd.read_excel(io='/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='communication')
    _nodes_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='pods')

    pods_data, pods2idx = load_pods(_pods_excel)
    nodes_data = load_nodes(_nodes_excel)
    comm_data = load_comm(_comm_excel)

    g = Graph(pods_data=pods_data, pod2idx=pods2idx, comm_data=comm_data, nodes_data=nodes_data)
    pod_affinity, node_affinity = g.cal_affinity()

    scheduler = MultiStageScheduler(pods_data=_pods_excel, nodes_data=_nodes_excel, pod_affinity=pod_affinity,
                                    node_affinity=node_affinity)
    ### schedule
    _plan = scheduler.schedule(enable_draw=True)

    ### check
    plan = scheduler.check_and_gen(scheduler, _plan)

    for _plan in plan:
        print(f'{_plan.__dict__}')


def test_parse_static_plan():
    _comm_excel = pd.read_excel(io='/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='communication')
    _nodes_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='pods')

    pods_data, pods2idx = load_pods(_pods_excel)
    nodes_data = load_nodes(_nodes_excel)
    comm_data = load_comm(_comm_excel)

    g = Graph(pods_data=pods_data, pod2idx=pods2idx, comm_data=comm_data, nodes_data=nodes_data)
    pod_affinity, node_affinity = g.cal_affinity()

    scheduler = MultiStageScheduler(pods_data=_pods_excel, nodes_data=_nodes_excel, pod_affinity=pod_affinity,
                                    node_affinity=node_affinity)
    ### schedule
    _plan = scheduler.schedule(enable_draw=True)

    ### check
    plan = scheduler.check_and_gen(scheduler, _plan)

    agents = read_excel_and_construct_agents(_pods_excel, plan)

    deploys = read_excel_and_generate_yamls(agents, _comm_excel)
    for _deploy in deploys:
        print(_deploy)


def test_parse_dynamic_plan():
    _comm_excel = pd.read_excel(io='/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='communication')
    _nodes_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='pods')

    pods_data, pods2idx = load_pods(_pods_excel)
    nodes_data = load_nodes(_nodes_excel)
    comm_data = load_comm(_comm_excel)

    g = Graph(pods_data=pods_data, pod2idx=pods2idx, comm_data=comm_data, nodes_data=nodes_data)
    pod_affinity, node_affinity = g.cal_affinity()

    scheduler = MultiStageScheduler(pods_data=_pods_excel, nodes_data=_nodes_excel, pod_affinity=pod_affinity,
                                    node_affinity=node_affinity)
    ### schedule
    _plan = scheduler.schedule(enable_draw=True)

    ### check
    plan = scheduler.check_and_gen(scheduler, _plan)

    agents = read_excel_and_construct_agents(_pods_excel, plan)

    deploys = read_excel_and_generate_yamls(agents, _comm_excel)
    for _deploy in deploys:
        print(_deploy)


def test_load_data():
    _comm_excel = pd.read_excel(io='/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='communication')
    _nodes_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
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
        if _pod.change_type == '-':
            pods_data.append(_pod)
            pod2idx.__setitem__(_pod.name, _pod2idx.get(_pod.name))
        else:
            pods_data.append(_pod)
            pod2idx.__setitem__(_pod.name, _pod2idx.get(_pod.name))

    # 静态调度过滤掉动态调度中交互关系变化数据,只过滤新增，不过滤删除
    for _comm in _comm_data:
        if _comm.change_type:
            if _task_comm.get(_comm.delay) is None:
                _task_comm.__setitem__(_comm.delay, [])
            _task_comm[_comm.delay].append(_comm)
        if _comm.change_type == '-':
            comm_data.append(_comm)
        else:
            comm_data.append(_comm)

    g = Graph(pods_data=pods_data, pod2idx=pod2idx, comm_data=comm_data, nodes_data=nodes_data)
    pod_affinity, node_affinity = g.cal_affinity()

    scheduler = MultiStageScheduler(pods_data=pods_data, nodes_data=nodes_data, pod_affinity=pod_affinity,
                                    node_affinity=node_affinity)
    ### schedule
    _plan = scheduler.schedule(enable_draw=False)

    ### check
    plan = scheduler.check_and_gen(scheduler, _plan)

    agents_info = NodeAgentsInfo.load(plan)


    print('Print 【NodeAgentsInfo】')
    for _agent_node_info in agents_info:
        print(f'{_agent_node_info}')

    print('Print 【InteractionDetail】')
    interaction_details = InteractionDetail.load(comm_data)
    for _interaction_detail in interaction_details:
        print(f'{_interaction_detail}')

    print('Print 【AffinityValue】')
    agents_affinity = AffinityValue.load(pod_affinity, pod2idx)
    for _agents_affinity in agents_affinity:
        print(f'{_agents_affinity}')





