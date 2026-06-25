import uuid
from datetime import datetime, timezone

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.student import Student
from app.schemas.student import StudentCreate
from app.api.v1.routers.students import create_student, get_student, delete_student
from fastapi import HTTPException
import pytest


@pytest.fixture
async def seeded_student(session):
    student = Student(id=uuid.uuid4(), name="Alice Smith")
    session.add(student)
    await session.flush()
    return student


async def test_create_student_generates_id(session):
    body = StudentCreate(name="Bob Jones")
    result = await create_student(body=body, session=session)
    assert result.id is not None
    assert result.name == "Bob Jones"


async def test_create_student_uses_provided_id(session):
    fixed_id = uuid.uuid4()
    body = StudentCreate(id=fixed_id, name="Alice Smith")
    result = await create_student(body=body, session=session)
    assert result.id == fixed_id


async def test_get_student_returns_student(session, seeded_student):
    result = await get_student(student_id=seeded_student.id, session=session)
    assert result.id == seeded_student.id
    assert result.name == seeded_student.name


async def test_get_student_raises_404_for_missing(session):
    with pytest.raises(HTTPException) as exc:
        await get_student(student_id=uuid.uuid4(), session=session)
    assert exc.value.status_code == 404


async def test_delete_student_removes_student(session, seeded_student):
    await delete_student(student_id=seeded_student.id, session=session)
    with pytest.raises(HTTPException) as exc:
        await get_student(student_id=seeded_student.id, session=session)
    assert exc.value.status_code == 404


async def test_delete_student_raises_404_for_missing(session):
    with pytest.raises(HTTPException) as exc:
        await delete_student(student_id=uuid.uuid4(), session=session)
    assert exc.value.status_code == 404


async def test_delete_student_cascades_to_documents_and_chunks(session, seeded_student):
    doc = Document(
        title="Test Doc",
        document_type="exam_spec",
        subject="Mathematics",
        level="A Level",
        source_url="test.pdf",
        student_id=seeded_student.id,
        uploaded_at=datetime.now(timezone.utc),
    )
    session.add(doc)
    await session.flush()

    chunk = Chunk(
        document_id=doc.id,
        content="Some content.",
        embedding=[0.1] * 1536,
        page_number=1,
        chunk_index=0,
    )
    session.add(chunk)
    await session.flush()

    await delete_student(student_id=seeded_student.id, session=session)

    with pytest.raises(HTTPException) as exc:
        await get_student(student_id=seeded_student.id, session=session)
    assert exc.value.status_code == 404
