from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    code: int = Field(200, description="状态码：200成功，4xx客户端错误，5xx服务端错误")
    msg: str = Field("success", description="提示信息")
    data: Optional[T] = Field(None, description="业务数据")
