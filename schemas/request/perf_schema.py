from typing import List, Optional
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field


class PerfQuery(BaseModel):
    model: Optional[str] = ''
    xAxis: List[str] = []
    yAxis: List[str] = []
