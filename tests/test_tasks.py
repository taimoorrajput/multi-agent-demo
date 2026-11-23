from collections.abc import Iterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client() -> Iterator[AsyncClient]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)


async def _create_project_and_user(client: AsyncClient) -> tuple[int, int]:
    # The projects/users tables exist in the schema, but their HTTP endpoints are owned by
    # other tickets (T-001/T-002) which aren't merged yet -- insert rows directly through the
    # overridden session instead of calling their (not-yet-existing) endpoints.
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        user_row = db.execute(
            text("INSERT INTO users (email, name) VALUES (:email, :name)"),
            {"email": f"owner-{uuid4().hex}@example.com", "name": "Demo Owner"},
        )
        db.commit()
        user_id = user_row.lastrowid

        project_row = db.execute(
            text("INSERT INTO projects (name, owner_id) VALUES (:name, :owner_id)"),
            {"name": "Demo Project", "owner_id": user_id},
        )
        db.commit()
        project_id = project_row.lastrowid
    finally:
        db.close()
    return project_id, user_id


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    project_id, _ = await _create_project_and_user(client)

    response = await client.post(
        "/tasks", json={"title": "Write docs", "description": "ADR notes", "project_id": project_id}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write docs"
    assert body["status"] == "todo"
    assert body["project_id"] == project_id
    assert body["assignee_id"] is None


@pytest.mark.asyncio
async def test_create_task_with_assignee(client: AsyncClient) -> None:
    project_id, user_id = await _create_project_and_user(client)

    response = await client.post(
        "/tasks",
        json={"title": "Write docs", "project_id": project_id, "assignee_id": user_id},
    )
    assert response.status_code == 201
    assert response.json()["assignee_id"] == user_id


@pytest.mark.asyncio
async def test_create_task_unknown_project(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": "Orphan task", "project_id": 999})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_task_unknown_assignee(client: AsyncClient) -> None:
    project_id, _ = await _create_project_and_user(client)

    response = await client.post(
        "/tasks", json={"title": "Orphan assignee", "project_id": project_id, "assignee_id": 999}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ASSIGNEE_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient) -> None:
    project_id, _ = await _create_project_and_user(client)
    created = await client.post("/tasks", json={"title": "Write docs", "project_id": project_id})
    task_id = created.json()["id"]

    response = await client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Write docs"


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient) -> None:
    response = await client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_patch_task_status(client: AsyncClient) -> None:
    project_id, _ = await _create_project_and_user(client)
    created = await client.post("/tasks", json={"title": "Write docs", "project_id": project_id})
    task_id = created.json()["id"]

    response = await client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_patch_task_invalid_status(client: AsyncClient) -> None:
    project_id, _ = await _create_project_and_user(client)
    created = await client.post("/tasks", json={"title": "Write docs", "project_id": project_id})
    task_id = created.json()["id"]

    response = await client.patch(f"/tasks/{task_id}", json={"status": "bogus"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_task_not_found(client: AsyncClient) -> None:
    response = await client.patch("/tasks/999", json={"status": "done"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_tasks_with_project_filter(client: AsyncClient) -> None:
    project_a_id, _ = await _create_project_and_user(client)
    project_b_id, _ = await _create_project_and_user(client)

    await client.post("/tasks", json={"title": "In project A", "project_id": project_a_id})
    await client.post("/tasks", json={"title": "In project B", "project_id": project_b_id})

    response = await client.get("/tasks", params={"project_id": project_a_id})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "In project A"

    response_all = await client.get("/tasks")
    assert response_all.status_code == 200
    assert len(response_all.json()) == 2
