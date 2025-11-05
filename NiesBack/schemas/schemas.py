from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import List

class GroupOut(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True

class GroupTreeOut(GroupOut):
    children: list["GroupTreeOut"] = Field(default_factory=list)

GroupTreeOut.model_rebuild()

class ReportAccessLevelEnum(str, Enum):
    gestao = "gestao"
    estrategico = "estrategico"
    operacional = "operacional"
    outros = "outros"

class   ReportOut(BaseModel):
    id: str | None = None
    name: str
    title_description: str | None = None
    description: str | None = None
    image_url: str | None = None
    powerbi_url: str | None = None
    workspace_id: str | None = None
    report_id: str | None = None
    group_id: str
    is_public: bool = True

    access_levels: List[ReportAccessLevelEnum] = Field(default_factory=list)


    class Config:
        from_attributes = True

