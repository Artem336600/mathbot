"""Tests for the Attachments API."""
import io
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mk_jpeg(name: str = "photo.jpg") -> tuple:
    """Return (filename, fileobj, content_type) for a tiny fake JPEG."""
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 20  # fake JPEG header
    return (name, io.BytesIO(data), "image/jpeg")


def _mk_pdf(name: str = "doc.pdf") -> tuple:
    """Return (filename, fileobj, content_type) for a fake PDF."""
    data = b"%PDF-1.4" + b"\x00" * 20
    return (name, io.BytesIO(data), "application/pdf")


def _mk_big_file(name: str = "big.jpg") -> tuple:
    """Return a fake file exceeding 20 MB."""
    data = b"\xff\xd8\xff\xe0" + b"X" * (21 * 1024 * 1024)
    return (name, io.BytesIO(data), "image/jpeg")


async def _create_topic(client: AsyncClient) -> int:
    resp = await client.post("/api/topics/", json={"title": "Test Topic"})
    assert resp.status_code == 200
    return resp.json()["id"]


async def _create_question(client: AsyncClient, topic_id: int) -> int:
    payload = {
        "topic_id": topic_id,
        "text": "Question?",
        "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
        "correct_option": "a",
        "difficulty": 1,
    }
    resp = await client.post("/api/questions/", json=payload)
    assert resp.status_code == 200
    return resp.json()["id"]


# ─── S3 mock helper ────────────────────────────────────────────────────────────

fake_upload = AsyncMock(return_value="fake/key.jpg")
fake_delete = AsyncMock(return_value=True)
fake_presigned = AsyncMock(return_value="http://fake-s3/presigned-url")


def patch_storage():
    return patch.multiple(
        "services.storage_service.StorageService",
        upload_file=fake_upload,
        delete_file=fake_delete,
        get_presigned_url=fake_presigned,
    )


# ─── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_photos_to_question(authed_client: AsyncClient):
    """Upload 2 JPEG photos to a question → should return 2 attachments."""
    topic_id = await _create_topic(authed_client)
    q_id = await _create_question(authed_client, topic_id)

    with patch_storage():
        resp = await authed_client.post(
            f"/api/attachments/question/{q_id}/upload",
            files=[("files", _mk_jpeg("a.jpg")), ("files", _mk_jpeg("b.jpg"))],
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    for att in data:
        assert att["attachment_type"] == "photo"
        assert att["entity_type"] == "question"
        assert att["entity_id"] == q_id
        assert "url" in att


@pytest.mark.asyncio
async def test_upload_docs_to_topic(authed_client: AsyncClient):
    """Upload a PDF to a topic → should succeed."""
    topic_id = await _create_topic(authed_client)

    with patch_storage():
        resp = await authed_client.post(
            f"/api/attachments/topic/{topic_id}/upload",
            files=[("files", _mk_pdf("report.pdf"))],
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["attachment_type"] == "document"
    assert data[0]["mime_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_doc_to_question_fails(authed_client: AsyncClient):
    """Uploading a PDF to a question → 400 (only photos allowed for questions)."""
    topic_id = await _create_topic(authed_client)
    q_id = await _create_question(authed_client, topic_id)

    with patch_storage():
        resp = await authed_client.post(
            f"/api/attachments/question/{q_id}/upload",
            files=[("files", _mk_pdf())],
        )

    assert resp.status_code == 400
    assert "Only photos" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_oversized_file_fails(authed_client: AsyncClient):
    """Uploading a >20 MB file → 400."""
    topic_id = await _create_topic(authed_client)

    with patch_storage():
        resp = await authed_client.post(
            f"/api/attachments/topic/{topic_id}/upload",
            files=[("files", _mk_big_file())],
        )

    assert resp.status_code == 400
    assert "20MB" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_entity_type(authed_client: AsyncClient):
    """entity_type='foo' → 400."""
    with patch_storage():
        resp = await authed_client.post(
            "/api/attachments/foo/1/upload",
            files=[("files", _mk_jpeg())],
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_attachments_for_entity(authed_client: AsyncClient):
    """GET /api/attachments/question/{id} returns the list of uploaded attachments."""
    topic_id = await _create_topic(authed_client)
    q_id = await _create_question(authed_client, topic_id)

    with patch_storage():
        # Upload first
        await authed_client.post(
            f"/api/attachments/question/{q_id}/upload",
            files=[("files", _mk_jpeg())],
        )
        # Then get
        resp = await authed_client.get(f"/api/attachments/question/{q_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["file_name"] == "photo.jpg"


@pytest.mark.asyncio
async def test_delete_attachment(authed_client: AsyncClient):
    """DELETE /api/attachments/{id} removes attachment from DB (and S3 mock)."""
    topic_id = await _create_topic(authed_client)
    q_id = await _create_question(authed_client, topic_id)

    with patch_storage():
        upload_resp = await authed_client.post(
            f"/api/attachments/question/{q_id}/upload",
            files=[("files", _mk_jpeg())],
        )
        att_id = upload_resp.json()[0]["id"]

        del_resp = await authed_client.delete(f"/api/attachments/{att_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        # Confirm it's gone
        list_resp = await authed_client.get(f"/api/attachments/question/{q_id}")
        assert list_resp.json() == []


@pytest.mark.asyncio
async def test_cascade_delete_on_topic_delete(authed_client: AsyncClient):
    """Deleting a topic also deletes its attachments (cascade via router)."""
    topic_id = await _create_topic(authed_client)

    with patch_storage():
        # Upload an attachment to the topic
        await authed_client.post(
            f"/api/attachments/topic/{topic_id}/upload",
            files=[("files", _mk_jpeg())],
        )

        # Delete topic
        del_resp = await authed_client.delete(f"/api/topics/{topic_id}")
        assert del_resp.status_code == 200

        # Attachment list should be empty (topic gone → attachments gone)
        list_resp = await authed_client.get(f"/api/attachments/topic/{topic_id}")
        assert list_resp.json() == []
