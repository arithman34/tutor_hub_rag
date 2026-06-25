from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentDetail, DocumentList, DocumentRead
from app.services.ingestion import ingest_document

router = APIRouter()


@router.post("", response_model=DocumentRead, status_code=201)
async def upload_document(
    file: UploadFile,
    title: str = Form(...),
    document_type: str = Form(...),
    subject: str = Form(...),
    level: str = Form(...),
    exam_board: str | None = Form(None),
    student_id: UUID | None = Form(None),
    session: AsyncSession = Depends(get_db),
) -> DocumentRead:
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    try:
        document = await ingest_document(
            session=session,
            file_bytes=file_bytes,
            title=title,
            document_type=document_type,
            subject=subject,
            level=level,
            source_filename=file.filename,
            exam_board=exam_board,
            student_id=student_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return DocumentRead.model_validate(document)


@router.get("", response_model=DocumentList)
async def list_documents(
    document_type: str | None = None,
    subject: str | None = None,
    level: str | None = None,
    exam_board: str | None = None,
    student_id: UUID | None = None,
    session: AsyncSession = Depends(get_db),
) -> DocumentList:
    stmt = select(Document)

    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    if subject:
        stmt = stmt.where(Document.subject == subject)
    if level:
        stmt = stmt.where(Document.level == level)
    if exam_board:
        stmt = stmt.where(Document.exam_board == exam_board)
    if student_id:
        stmt = stmt.where(Document.student_id == student_id)

    documents = (await session.execute(stmt)).scalars().all()
    return DocumentList(
        items=[DocumentRead.model_validate(d) for d in documents],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> DocumentDetail:
    stmt = (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.chunks))
    )
    document = (await session.execute(stmt)).scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentDetail.model_validate(document)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    stmt = select(Document).where(Document.id == document_id)
    document = (await session.execute(stmt)).scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    await session.delete(document)
    await session.commit()
