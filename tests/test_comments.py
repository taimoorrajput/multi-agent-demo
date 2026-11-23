from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.task import Task
from app.models.user import User

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)


@pytest.fixture
def task_and_author() -> tuple[int, int]:
    db = TestingSessionLocal()
    task = Task(title="Write docs")
    user = User(email=f"author-{uuid.uuid4()}@example.com", name="Author")
    db.add_all([task, user])
    db.commit()
    db.refresh(task)
    db.refresh(user)
    ids = (task.id, user.id)
    db.close()
    return ids


def test_create_comment_success(task_and_author: tuple[int, int]) -> None:
    task_id, author_id = task_and_author
    resp = client.post(f"/tasks/{task_id}/comments", json={"body": "nice work", "author_id": author_id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "nice work"
    assert data["task_id"] == task_id
    assert data["author_id"] == author_id
    assert "id" in data
    assert "created_at" in data


def test_create_comment_task_not_found(task_and_author: tuple[int, int]) -> None:
    _, author_id = task_and_author
    resp = client.post("/tasks/999999/comments", json={"body": "x", "author_id": author_id})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "TASK_NOT_FOUND"


def test_create_comment_author_not_found(task_and_author: tuple[int, int]) -> None:
    task_id, _ = task_and_author
    resp = client.post(f"/tasks/{task_id}/comments", json={"body": "x", "author_id": 999999})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "AUTHOR_NOT_FOUND"


def test_list_comments_ordered_oldest_first(task_and_author: tuple[int, int]) -> None:
    task_id, author_id = task_and_author
    client.post(f"/tasks/{task_id}/comments", json={"body": "first", "author_id": author_id})
    client.post(f"/tasks/{task_id}/comments", json={"body": "second", "author_id": author_id})

    resp = client.get(f"/tasks/{task_id}/comments")
    assert resp.status_code == 200
    bodies = [c["body"] for c in resp.json()]
    assert bodies == ["first", "second"]


def test_list_comments_task_not_found() -> None:
    resp = client.get("/tasks/999999/comments")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "TASK_NOT_FOUND"


def test_delete_comment_success(task_and_author: tuple[int, int]) -> None:
    task_id, author_id = task_and_author
    created = client.post(
        f"/tasks/{task_id}/comments", json={"body": "to delete", "author_id": author_id}
    ).json()

    resp = client.delete(f"/comments/{created['id']}")
    assert resp.status_code == 204

    remaining = client.get(f"/tasks/{task_id}/comments").json()
    assert created["id"] not in [c["id"] for c in remaining]


def test_delete_comment_not_found() -> None:
    resp = client.delete("/comments/999999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "COMMENT_NOT_FOUND"
