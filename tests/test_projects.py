from collections.abc import Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
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


async def _create_owner(client: AsyncClient, email: str = "owner@example.com") -> int:
    response = await client.post("/users", json={"email": email, "name": "Owner"})
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient) -> None:
    owner_id = await _create_owner(client)
    response = await client.post(
        "/projects", json={"name": "Demo", "description": "desc", "owner_id": owner_id}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Demo"
    assert body["description"] == "desc"
    assert body["owner_id"] == owner_id
    assert "id" in body


@pytest.mark.asyncio
async def test_create_project_unknown_owner(client: AsyncClient) -> None:
    response = await client.post(
        "/projects", json={"name": "Demo", "description": None, "owner_id": 999}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OWNER_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_project_missing_name(client: AsyncClient) -> None:
    owner_id = await _create_owner(client)
    response = await client.post("/projects", json={"owner_id": owner_id})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient) -> None:
    owner_id = await _create_owner(client)
    created = await client.post(
        "/projects", json={"name": "Demo", "description": "desc", "owner_id": owner_id}
    )
    project_id = created.json()["id"]

    response = await client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Demo"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient) -> None:
    response = await client.get("/projects/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient) -> None:
    owner_id = await _create_owner(client)
    await client.post("/projects", json={"name": "A", "description": None, "owner_id": owner_id})
    await client.post("/projects", json={"name": "B", "description": None, "owner_id": owner_id})

    response = await client.get("/projects")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_projects_filter_by_owner(client: AsyncClient) -> None:
    owner1 = await _create_owner(client, "a@example.com")
    owner2 = await _create_owner(client, "b@example.com")
    await client.post("/projects", json={"name": "A1", "description": None, "owner_id": owner1})
    await client.post("/projects", json={"name": "B1", "description": None, "owner_id": owner2})

    response = await client.get("/projects", params={"owner_id": owner1})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["owner_id"] == owner1
