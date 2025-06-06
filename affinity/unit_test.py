from affinity.calculate import Graph
import pandas as pd

from affinity.multi_stage_scheduler import MultiStageScheduler

from affinity.parse_schedule import read_excel_and_construct_agents, read_excel_and_generate_yamls


def test_calculate_affinity():
    _comm_excel = pd.read_excel(io='/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='communication')
    _nodes_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                 sheet_name='nodes')
    _pods_excel = pd.read_excel('/Users/amethyst/PycharmProjects/affinity-model/data/亲和性试验配置.xlsx',
                                sheet_name='pods')

    g = Graph(pods_data=_pods_excel, comm_data=_comm_excel, nodes_data=_nodes_excel)
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

    g = Graph(pods_data=_pods_excel, comm_data=_comm_excel, nodes_data=_nodes_excel)
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

    g = Graph(pods_data=_pods_excel, comm_data=_comm_excel, nodes_data=_nodes_excel)
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

    g = Graph(pods_data=_pods_excel, comm_data=_comm_excel, nodes_data=_nodes_excel)
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
