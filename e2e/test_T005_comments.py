"""E2E for T-005: comment on a task through Swagger UI.

Creates a task + user directly via the app's DB session (no T-002/T-003/T-001 endpoints
required yet), then drives POST/GET /tasks/{task_id}/comments through Swagger.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # e2e/ has no __init__.py

from app.db import SessionLocal
from app.models.task import Task
from app.models.user import User


@pytest.fixture
def task_and_author() -> tuple[int, int]:
    db = SessionLocal()
    task = Task(title="Record the demo")
    user = User(email="e2e-author@example.com")
    db.add_all([task, user])
    db.commit()
    db.refresh(task)
    db.refresh(user)
    ids = (task.id, user.id)
    db.close()
    return ids


def test_T005_create_and_list_comments(swagger, task_and_author: tuple[int, int]) -> None:
    task_id, author_id = task_and_author

    created = swagger.call(
        "POST",
        "/tasks/{task_id}/comments",
        params={"task_id": str(task_id)},
        body=json.dumps({"body": "Looks good to me", "author_id": author_id}),
        expect_status=201,
    )
    assert json.loads(created)["body"] == "Looks good to me"

    swagger.page.reload()
    listed = swagger.call(
        "GET",
        "/tasks/{task_id}/comments",
        params={"task_id": str(task_id)},
        expect_status=200,
    )
    comments = json.loads(listed)
    assert len(comments) == 1
    assert comments[0]["body"] == "Looks good to me"
