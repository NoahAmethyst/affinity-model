# 定义响应模型
from typing import Optional, Any

from humanfriendly.terminal import message
from pydantic import BaseModel


class ScheduleReq(BaseModel):
    exp_id: int


class BaseResponse(BaseModel):
    data: Optional[Any] = None
    message: Optional[str]
    code: Optional[int]

    @staticmethod
    def _ok(data: Optional[Any] = None, message: Optional[str] = None) -> 'BaseResponse':
        return BaseResponse(
            data=data,
            message=message,
            code=200
        )

    @staticmethod
    def _error(message: Optional[str] = None) -> 'BaseResponse':
        return BaseResponse(
            data=None,
            message=message,
            code=500
        )
