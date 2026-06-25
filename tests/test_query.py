from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas.query import QueryFilters
from app.services.query import answer_question


@pytest.fixture
async def seeded(session):
    doc = Document(
        title="Maths Spec",
        document_type="exam_spec",
        subject="Mathematics",
        level="A Level",
        exam_board="Edexcel",
        source_url="maths_spec.pdf",
        uploaded_at=datetime.now(timezone.utc),
    )
    session.add(doc)
    await session.flush()

    chunk = Chunk(
        document_id=doc.id,
        content="The derivative of x squared is 2x.",
        embedding=[0.1] * 1536,
        page_number=1,
        chunk_index=0,
    )
    session.add(chunk)
    await session.flush()
    return doc, chunk


async def test_answer_question_no_chunks_returns_fallback(session):
    with patch(
        "app.services.query.embed_question",
        new=AsyncMock(return_value=[0.0] * 1536),
    ):
        response = await answer_question(session, "What is integration?", QueryFilters())

    assert response.answer == "No relevant content found for your question."
    assert response.sources == []


async def test_answer_question_returns_answer_and_sources(session, seeded):
    doc, _ = seeded
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "The derivative of x^2 is 2x."

    with (
        patch(
            "app.services.query.embed_question",
            new=AsyncMock(return_value=[0.1] * 1536),
        ),
        patch("app.services.query.client") as mock_client,
    ):
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        response = await answer_question(
            session, "What is the derivative of x squared?", QueryFilters()
        )

    assert "2x" in response.answer
    assert len(response.sources) == 1
    assert response.sources[0].title == "Maths Spec"
    assert response.sources[0].page_number == 1


async def test_answer_question_filters_by_subject(session, seeded):
    with patch(
        "app.services.query.embed_question",
        new=AsyncMock(return_value=[0.1] * 1536),
    ):
        # filter for a subject that doesn't exist
        response = await answer_question(
            session, "What is calculus?", QueryFilters(subject="Physics")
        )

    assert response.answer == "No relevant content found for your question."
    assert response.sources == []
