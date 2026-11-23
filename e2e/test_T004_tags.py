"""E2E for T-004: attach and list tags on a task via Swagger UI.

Task creation isn't available through the API yet (needs T-001/T-002/T-003 merged), so this
test seeds a task row directly in the SQLite file the live app reads, using the stdlib
sqlite3 module (the e2e package has no `app` import path, unlike tests/).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("app.db")


def _seed_task() -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS task_tags ("
            "task_id INTEGER NOT NULL REFERENCES tasks(id), "
            "tag_id INTEGER NOT NULL REFERENCES tags(id), "
            "PRIMARY KEY (task_id, tag_id))"
        )
        cursor = conn.execute("INSERT INTO tasks (title) VALUES (?)", ("E2E seed task",))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def test_T004_attach_and_list_tags(swagger):
    task_id = _seed_task()

    attached = swagger.call(
        "POST", "/tasks/{task_id}/tags",
        params={"task_id": str(task_id)},
        body=json.dumps({"name": "urgent"}),
        expect_status=201,
    )
    assert json.loads(attached)["name"] == "urgent"

    swagger.page.reload()
    listed = swagger.call(
        "GET", "/tasks/{task_id}/tags",
        params={"task_id": str(task_id)},
        expect_status=200,
    )
    names = [tag["name"] for tag in json.loads(listed)]
    assert "urgent" in names
