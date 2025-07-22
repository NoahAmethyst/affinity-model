from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

import affinity
from affinity import exec_schedule
from affinity.parse_schedule import generate_single
from affinity.schedule_operator import terminate_schedule, operate_schedule
from api.model import BaseResponse
import service.affinity_tool_service as affinity_tool_service
import service.models.affinity_tool_models as affinity_tool_models

# 创建一个路由分组
affinity_model = APIRouter(
    prefix="/affinity",
    tags=["亲和性模型"],
)


@affinity_model.post("/start_schedule/{exp_id}/{is_base}", response_model=BaseResponse,
                     summary="开启调度任务",
                     tags=['亲和性模型'])
async def start_schedule(exp_id: int, is_base: int, file: UploadFile = File(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    # 检查文件类型
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 文件格式"
        )
    affinity_tool_service.report_event(exp_id=exp_id, _type=affinity_tool_models.EventType.EXPERIMENT_START)
    contents = file.file.read()
    background_tasks.add_task(exec_schedule, exp_id=exp_id, contents=contents, base=(is_base == 1))

    return BaseResponse._ok(message='接受到亲和性调度配置文件，开始处理')


@affinity_model.post("/start_schedule_base/{exp_id}", response_model=BaseResponse,
                     summary="开启基准调度任务",
                     tags=['亲和性模型'])
async def start_schedule(exp_id: int, file: UploadFile = File(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    # 检查文件类型
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 文件格式"
        )
    affinity_tool_service.report_event(exp_id=exp_id, _type=affinity_tool_models.EventType.EXPERIMENT_START)
    contents = file.file.read()
    background_tasks.add_task(exec_schedule, exp_id=exp_id, contents=contents, base=True)

    return BaseResponse._ok(message='接受到亲和性调度配置文件，开始处理')


@affinity_model.post("/dynamic_schedule/{exp_id}", response_model=BaseResponse,
                     summary="开启基准调度任务",
                     tags=['亲和性模型'])
async def start_schedule(exp_id: int, file: UploadFile = File(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    # 检查文件类型
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 文件格式"
        )
    affinity_tool_service.report_event(exp_id=exp_id, _type=affinity_tool_models.EventType.EXPERIMENT_START)
    contents = file.file.read()
    background_tasks.add_task(exec_schedule, exp_id=exp_id, contents=contents, base=True)

    return BaseResponse._ok(message='接受到亲和性调度配置文件，开始处理')


@affinity_model.post("/schedule/plan/{exp_id}/{is_base}", response_model=BaseResponse,
                     summary="动态调度",
                     tags=['亲和性模型'])
async def schedule_plan(exp_id: int, is_base: int, agents: list[str], nodes: list[str],
                        background_tasks: BackgroundTasks = BackgroundTasks()):
    background_tasks.add_task(affinity.schedule_plan, exp_id=exp_id, new_pods=agents, nodes=nodes, is_base=is_base == 1)

    return BaseResponse._ok()


class Allocate(BaseModel):
    exp_id: int
    node: str
    pod: str


@affinity_model.post("/schedule/allocate", response_model=BaseResponse,
                     summary="更改节点",
                     tags=['亲和性模型'])
async def allocate_node(allocate: Allocate):
    # 上报执行动态调整策略
    affinity_tool_service.report_event(exp_id=allocate.exp_id,
                                       _type=affinity_tool_models.EventType.DYNAMIC_SCHEDULING_POLICY_EXECUTION)

    deploys = []
    deploy = generate_single(allocate.node, allocate.pod)
    deploys.append(deploy)
    operate_schedule(exp_id=allocate.exp_id, deploys=deploys)

    return BaseResponse._ok()


@affinity_model.post("/dynamic_schedule/{exp_id}", response_model=BaseResponse,
                     summary="开启基准调度任务",
                     tags=['亲和性模型'])
async def start_schedule(exp_id: int, file: UploadFile = File(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    # 检查文件类型
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 文件格式"
        )
    affinity_tool_service.report_event(exp_id=exp_id, _type=affinity_tool_models.EventType.EXPERIMENT_START)
    contents = file.file.read()
    background_tasks.add_task(exec_schedule, exp_id=exp_id, contents=contents, base=True)

    return BaseResponse._ok(message='接受到亲和性调度配置文件，开始处理')


@affinity_model.delete("/stop_schedule/{exp_id}", response_model=BaseResponse,
                       summary="停止调度",
                       tags=['亲和性模型'])
async def stop_schedule(exp_id: int, background_tasks: BackgroundTasks = BackgroundTasks()):
    affinity_tool_service.report_event(exp_id=exp_id, _type=affinity_tool_models.EventType.EXPERIMENT_END)
    background_tasks.add_task(terminate_schedule, exp_id=exp_id)
    return BaseResponse._ok()
