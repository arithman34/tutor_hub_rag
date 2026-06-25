from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: UUID
    title: str
    document_type: str
    subject: str
    level: str
    exam_board: str | None
    student_id: UUID | None
    source_url: str | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ChunkRead(BaseModel):
    id: UUID
    content: str
    page_number: int | None
    chunk_index: int

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentRead):
    chunks: list[ChunkRead]


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int
