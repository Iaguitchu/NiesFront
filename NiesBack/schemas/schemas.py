from pydantic import BaseModel, Field

class GroupOut(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True

class GroupTreeOut(GroupOut):
    children: list["GroupTreeOut"] = Field(default_factory=list)

GroupTreeOut.model_rebuild()

class ReportOut(BaseModel):
    id: str
    name: str
    thumbnail_url: str | None = None
    title_description: str | None = None
    description: str | None = None
    image_url: str | None = None
    class Config:
        from_attributes = True
