from __future__ import annotations

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.errors import ApiError
from app.main import app
from app.models.task import Task

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@app.exception_handler(ApiError)
async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    # Stand-in for T-001's ADR-0003 handler, which isn't wired into app/main.py yet.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _create_task(title: str = "Test task") -> int:
    db = TestingSessionLocal()
    task = Task(title=title)
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id
    db.close()
    return task_id


def test_attach_tag_to_missing_task_returns_404():
    response = client.post("/tasks/999/tags", json={"name": "urgent"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


def test_attach_new_tag_creates_it():
    task_id = _create_task()
    response = client.post(f"/tasks/{task_id}/tags", json={"name": "urgent"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "urgent"
    assert "id" in body


def test_attach_same_tag_twice_is_idempotent():
    task_id = _create_task()
    first = client.post(f"/tasks/{task_id}/tags", json={"name": "urgent"})
    second = client.post(f"/tasks/{task_id}/tags", json={"name": "urgent"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    tags = client.get(f"/tasks/{task_id}/tags").json()
    assert len(tags) == 1


def test_list_tags_for_task():
    task_id = _create_task()
    client.post(f"/tasks/{task_id}/tags", json={"name": "urgent"})
    client.post(f"/tasks/{task_id}/tags", json={"name": "backend"})

    response = client.get(f"/tasks/{task_id}/tags")
    assert response.status_code == 200
    names = {tag["name"] for tag in response.json()}
    assert names == {"urgent", "backend"}


def test_list_tags_for_missing_task_returns_404():
    response = client.get("/tasks/999/tags")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


def test_detach_tag():
    task_id = _create_task()
    created = client.post(f"/tasks/{task_id}/tags", json={"name": "urgent"}).json()

    response = client.delete(f"/tasks/{task_id}/tags/{created['id']}")
    assert response.status_code == 204

    tags = client.get(f"/tasks/{task_id}/tags").json()
    assert tags == []


def test_detach_missing_tag_returns_404():
    task_id = _create_task()
    response = client.delete(f"/tasks/{task_id}/tags/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TAG_NOT_FOUND"
