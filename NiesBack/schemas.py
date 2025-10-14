from pydantic import BaseModel

class GroupOut(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True  # pydantic v2
