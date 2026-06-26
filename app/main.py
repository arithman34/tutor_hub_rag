from fastapi import Depends, FastAPI

from app.api.v1.routers.documents import router as documents_router
from app.api.v1.routers.query import router as query_router
from app.api.v1.routers.students import router as students_router
from app.core.config import settings
from app.core.security import verify_api_key

app = FastAPI(title="TutorHub RAG API", version="1.0.0")

app.include_router(students_router, prefix=f"{settings.api_prefix}/students", tags=["students"], dependencies=[Depends(verify_api_key)])
app.include_router(documents_router, prefix=f"{settings.api_prefix}/documents", tags=["documents"], dependencies=[Depends(verify_api_key)])
app.include_router(query_router, prefix=f"{settings.api_prefix}/query", tags=["query"], dependencies=[Depends(verify_api_key)])


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
