from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks

from affinity import exec_schedule
from api.model import UploadResponse
from util.logger import report_event, EventType

# 创建一个路由分组
affinity_model = APIRouter(
    prefix="/affinity",
    tags=["亲和性模型"],
    responses={404: {"description": "Not found"}}
)


@affinity_model.post("/start_schedule/{exp_id}", response_model=UploadResponse)
async def start_schedule(exp_id: int, file: UploadFile = File(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    # 检查文件类型
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 .xlsx 文件格式"
        )
    report_event(exp_id=exp_id, _type=EventType.EXPERIMENT_START)
    contents = file.file.read()
    background_tasks.add_task(exec_schedule, exp_id=exp_id, contents=contents)

    return UploadResponse(
        filename=file.filename,
        content_type=file.content_type,
        message="文件上传和处理成功",
    )
