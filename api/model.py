# 定义响应模型
from typing import Optional

from pydantic import BaseModel


class ScheduleReq(BaseModel):
    exp_id: int


class UploadResponse(BaseModel):
    filename: str
    content_type: str
    message: str
    data: Optional[dict] = None
