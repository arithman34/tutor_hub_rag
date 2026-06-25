from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query import answer_question

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    session: AsyncSession = Depends(get_db),
) -> QueryResponse:
    return await answer_question(
        session=session,
        question=body.question,
        filters=body.filters,
    )
