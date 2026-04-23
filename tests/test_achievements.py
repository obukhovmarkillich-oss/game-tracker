import pytest
from httpx import AsyncClient, ASGITransport

from app import create_app
from tests.conftest import TestEngine


@pytest.fixture
def app():
    return create_app(_engine=TestEngine)


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def auth_headers(client):
    async def _get_headers(username="testuser", email="test@example.com", password="password123"):
        await client.post("/api/register", json={
            "username": username,
            "email": email,
            "password": password,
        })
        response = await client.post("/api/login", json={
            "username": username,
            "password": password,
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _get_headers


@pytest.mark.asyncio
async def test_create_achievement(client, auth_headers):
    headers = await auth_headers()
    game_resp = await client.post("/api/games", json={"title": "Skyrim"}, headers=headers)
    game_id = game_resp.json()["id"]

    response = await client.post(f"/api/games/{game_id}/achievements", json={
        "name": "Dragon Soul",
        "description": "Absorbed a dragon soul",
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dragon Soul"
    assert data["game_id"] == game_id
    assert data["is_earned"] is False


@pytest.mark.asyncio
async def test_create_achievement_without_auth(client):
    response = await client.post("/api/games/1/achievements", json={"name": "Test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_achievement_game_not_found(client, auth_headers):
    headers = await auth_headers()
    response = await client.post("/api/games/99999/achievements", json={"name": "Test"}, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_achievement(client, auth_headers):
    headers = await auth_headers()
    game_resp = await client.post("/api/games", json={"title": "Oblivion"}, headers=headers)
    game_id = game_resp.json()["id"]

    ach_resp = await client.post(f"/api/games/{game_id}/achievements", json={
        "name": "First Quest",
        "is_earned": False,
    }, headers=headers)
    achievement_id = ach_resp.json()["id"]

    response = await client.put(f"/api/achievements/{achievement_id}", json={
        "is_earned": True,
        "date_earned": "2024-06-15",
    }, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_earned"] is True
    assert str(data["date_earned"]) == "2024-06-15"


@pytest.mark.asyncio
async def test_update_achievement_not_found(client, auth_headers):
    headers = await auth_headers()
    response = await client.put("/api/achievements/99999", json={"is_earned": True}, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_achievement(client, auth_headers):
    headers = await auth_headers()
    game_resp = await client.post("/api/games", json={"title": "Fallout 4"}, headers=headers)
    game_id = game_resp.json()["id"]

    ach_resp = await client.post(f"/api/games/{game_id}/achievements", json={"name": "Scavenger"}, headers=headers)
    achievement_id = ach_resp.json()["id"]

    response = await client.delete(f"/api/achievements/{achievement_id}", headers=headers)
    assert response.status_code == 204

    response = await client.put(f"/api/achievements/{achievement_id}", json={"is_earned": True}, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_achievement_stats(client, auth_headers):
    headers = await auth_headers()
    game_resp = await client.post("/api/games", json={"title": "Zelda"}, headers=headers)
    game_id = game_resp.json()["id"]

    await client.post(f"/api/games/{game_id}/achievements", json={
        "name": "A", "is_earned": True,
    }, headers=headers)
    await client.post(f"/api/games/{game_id}/achievements", json={
        "name": "B", "is_earned": True,
    }, headers=headers)
    await client.post(f"/api/games/{game_id}/achievements", json={
        "name": "C", "is_earned": False,
    }, headers=headers)

    response = await client.get("/api/stats", headers=headers)
    data = response.json()
    assert data["total_achievements"] == 3
    assert data["earned_achievements"] == 2


@pytest.mark.asyncio
async def test_delete_game_cascades_achievements(client, auth_headers):
    headers = await auth_headers()
    game_resp = await client.post("/api/games", json={"title": "Metroid"}, headers=headers)
    game_id = game_resp.json()["id"]

    await client.post(f"/api/games/{game_id}/achievements", json={"name": "X"}, headers=headers)

    response = await client.delete(f"/api/games/{game_id}", headers=headers)
    assert response.status_code == 204
