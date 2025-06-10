from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks

from affinity import exec_schedule
from affinity.schedule_operator import terminate_schedule
from api.model import BaseResponse
import service.affinity_tool_service as affinity_tool_service
import service.models.affinity_tool_models as affinity_tool_models

# 创建一个路由分组
affinity_model = APIRouter(
    prefix="/affinity",
    tags=["亲和性模型"],
)


@affinity_model.post("/start_schedule/{exp_id}", response_model=BaseResponse,
                     summary="开启调度任务",
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
    background_tasks.add_task(exec_schedule, exp_id=exp_id, contents=contents)

    return BaseResponse._ok(message='接受到亲和性调度配置文件，开始处理')


@affinity_model.delete("/stop_schedule/{exp_id}", response_model=BaseResponse,
                       summary="停止调度",
                       tags=['亲和性模型'])
async def stop_schedule(exp_id: int, background_tasks: BackgroundTasks = BackgroundTasks()):
    affinity_tool_service.report_event(exp_id=exp_id, _type=affinity_tool_models.EventType.EXPERIMENT_END)
    background_tasks.add_task(terminate_schedule, exp_id=exp_id)
    return BaseResponse._ok()
