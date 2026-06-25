import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentRead

router = APIRouter()


@router.post("", response_model=StudentRead, status_code=201)
async def create_student(
    body: StudentCreate,
    session: AsyncSession = Depends(get_db),
) -> StudentRead:
    student = Student(
        id=body.id or uuid.uuid4(),
        name=body.name,
    )
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return StudentRead.model_validate(student)


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StudentRead:
    student = (
        await session.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    return StudentRead.model_validate(student)


@router.delete("/{student_id}", status_code=204)
async def delete_student(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    student = (
        await session.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    await session.delete(student)
    await session.commit()
