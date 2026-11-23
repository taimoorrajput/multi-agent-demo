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


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    response = await client.post("/users", json={"email": "a@example.com", "name": "Alice"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "a@example.com"
    assert body["name"] == "Alice"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient) -> None:
    await client.post("/users", json={"email": "a@example.com", "name": "Alice"})
    response = await client.post("/users", json={"email": "a@example.com", "name": "Bob"})
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "USER_EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient) -> None:
    created = await client.post("/users", json={"email": "a@example.com", "name": "Alice"})
    user_id = created.json()["id"]

    response = await client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "a@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient) -> None:
    response = await client.get("/users/999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient) -> None:
    await client.post("/users", json={"email": "a@example.com", "name": "Alice"})
    await client.post("/users", json={"email": "b@example.com", "name": "Bob"})

    response = await client.get("/users")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {u["email"] for u in body} == {"a@example.com", "b@example.com"}
