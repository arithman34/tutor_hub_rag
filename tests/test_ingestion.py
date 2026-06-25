from unittest.mock import AsyncMock, patch

import pytest

from app.services.ingestion import chunk_text, ingest_document


def test_chunk_text_short_text_produces_one_chunk():
    result = chunk_text("short text", page_number=1)
    assert len(result) == 1
    assert result[0]["content"] == "short text"
    assert result[0]["page_number"] == 1
    assert result[0]["chunk_index"] == 0


def test_chunk_text_splits_at_chunk_size():
    text = "a" * 900
    result = chunk_text(text, page_number=2)
    assert len(result) == 2
    assert result[0]["content"] == "a" * 800
    assert result[1]["content"] == "a" * 200
    assert result[1]["chunk_index"] == 1
    assert result[1]["page_number"] == 2


def test_chunk_text_overlap_carries_content():
    # first 800 chars are 'a', last 200 are 'b'
    text = "a" * 800 + "b" * 200
    result = chunk_text(text, page_number=3)
    assert result[0]["content"] == "a" * 800
    # second chunk: offset 700, so 100 a's then 200 b's
    assert result[1]["content"] == "a" * 100 + "b" * 200


async def test_ingest_document_persists_document_and_chunks(session):
    fake_pages = [("The derivative of x squared is 2x.", 1)]
    fake_embedding = [0.1] * 1536

    with (
        patch("app.services.ingestion.extract_pages", return_value=fake_pages),
        patch(
            "app.services.ingestion.embed_texts",
            new=AsyncMock(return_value=[fake_embedding]),
        ),
    ):
        doc = await ingest_document(
            session=session,
            file_bytes=b"fake-pdf-bytes",
            title="Calculus Notes",
            document_type="session_notes",
            subject="Mathematics",
            level="A Level",
            source_filename="calculus.pdf",
        )

    assert doc.id is not None
    assert doc.title == "Calculus Notes"
    assert doc.subject == "Mathematics"


async def test_ingest_document_raises_for_empty_pdf(session):
    with patch("app.services.ingestion.extract_pages", return_value=[]):
        with pytest.raises(ValueError, match="No text could be extracted"):
            await ingest_document(
                session=session,
                file_bytes=b"fake-pdf-bytes",
                title="Empty PDF",
                document_type="PDF",
                subject="Mathematics",
                level="A Level",
                source_filename="empty.pdf",
            )
