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
async def test_create_game(client, auth_headers):
    headers = await auth_headers()
    response = await client.post("/api/games", json={
        "title": "The Witcher 3",
        "platform": "PC",
        "tags": "RPG, Open World",
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "The Witcher 3"
    assert data["platform"] == "PC"
    assert data["tags"] == "RPG, Open World"
    assert data["play_time_minutes"] == 0


@pytest.mark.asyncio
async def test_create_game_without_auth(client):
    response = await client.post("/api/games", json={"title": "No Auth Game"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_games(client, auth_headers):
    headers = await auth_headers()
    await client.post("/api/games", json={"title": "Game 1"}, headers=headers)
    await client.post("/api/games", json={"title": "Game 2"}, headers=headers)

    response = await client.get("/api/games", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["size"] == 10


@pytest.mark.asyncio
async def test_list_games_pagination(client, auth_headers):
    headers = await auth_headers()
    for i in range(15):
        await client.post("/api/games", json={"title": f"Game {i}"}, headers=headers)

    response = await client.get("/api/games?page=1&size=5", headers=headers)
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5
    assert data["pages"] == 3

    response = await client.get("/api/games?page=2&size=5", headers=headers)
    data = response.json()
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_get_game(client, auth_headers):
    headers = await auth_headers()
    create_resp = await client.post("/api/games", json={"title": "Elden Ring"}, headers=headers)
    game_id = create_resp.json()["id"]

    response = await client.get(f"/api/games/{game_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Elden Ring"


@pytest.mark.asyncio
async def test_get_game_not_found(client, auth_headers):
    headers = await auth_headers()
    response = await client.get("/api/games/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_game(client, auth_headers):
    headers = await auth_headers()
    create_resp = await client.post("/api/games", json={"title": "Old Title"}, headers=headers)
    game_id = create_resp.json()["id"]

    response = await client.put(f"/api/games/{game_id}", json={"title": "New Title", "rating": 9}, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["rating"] == 9


@pytest.mark.asyncio
async def test_delete_game(client, auth_headers):
    headers = await auth_headers()
    create_resp = await client.post("/api/games", json={"title": "To Delete"}, headers=headers)
    game_id = create_resp.json()["id"]

    response = await client.delete(f"/api/games/{game_id}", headers=headers)
    assert response.status_code == 204

    response = await client.get(f"/api/games/{game_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_playtime(client, auth_headers):
    headers = await auth_headers()
    create_resp = await client.post("/api/games", json={"title": "Dark Souls"}, headers=headers)
    game_id = create_resp.json()["id"]

    response = await client.patch(f"/api/games/{game_id}/playtime", json={"minutes_to_add": 120}, headers=headers)
    assert response.status_code == 200
    assert response.json()["play_time_minutes"] == 120

    response = await client.patch(f"/api/games/{game_id}/playtime", json={"minutes_to_add": 60}, headers=headers)
    assert response.json()["play_time_minutes"] == 180


@pytest.mark.asyncio
async def test_filter_games_by_tag(client, auth_headers):
    headers = await auth_headers()
    await client.post("/api/games", json={"title": "Game A", "tags": "RPG, Fantasy"}, headers=headers)
    await client.post("/api/games", json={"title": "Game B", "tags": "Shooter, FPS"}, headers=headers)
    await client.post("/api/games", json={"title": "Game C", "tags": "RPG, Action"}, headers=headers)

    response = await client.get("/api/games?tag=RPG", headers=headers)
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_filter_games_by_rating(client, auth_headers):
    headers = await auth_headers()
    await client.post("/api/games", json={"title": "Game A", "rating": 3}, headers=headers)
    await client.post("/api/games", json={"title": "Game B", "rating": 7}, headers=headers)
    await client.post("/api/games", json={"title": "Game C", "rating": 9}, headers=headers)

    response = await client.get("/api/games?min_rating=7", headers=headers)
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_stats_empty(client, auth_headers):
    headers = await auth_headers()
    response = await client.get("/api/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_play_time_minutes"] == 0
    assert data["games_count"] == 0
    assert data["total_achievements"] == 0


@pytest.mark.asyncio
async def test_stats_with_data(client, auth_headers):
    headers = await auth_headers()
    await client.post("/api/games", json={"title": "Game 1", "play_time_minutes": 600, "rating": 8}, headers=headers)
    await client.post("/api/games", json={"title": "Game 2", "play_time_minutes": 300, "rating": 10}, headers=headers)

    response = await client.get("/api/stats", headers=headers)
    data = response.json()
    assert data["total_play_time_minutes"] == 900
    assert data["total_play_time_hours"] == 15.0
    assert data["games_count"] == 2
    assert data["average_rating"] == 9.0
    assert len(data["top_games"]) == 2
    assert data["top_games"][0]["title"] == "Game 1"


@pytest.mark.asyncio
async def test_search(client):
    response = await client.get("/api/search?q=witcher&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "witcher"
    assert "results" in data
