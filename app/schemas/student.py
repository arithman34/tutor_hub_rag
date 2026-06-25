from uuid import UUID

from pydantic import BaseModel


class StudentCreate(BaseModel):
    id: UUID | None = None
    name: str


class StudentRead(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}
