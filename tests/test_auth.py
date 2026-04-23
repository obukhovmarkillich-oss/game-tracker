import os
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





@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post("/api/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client, test_user):
    response = await client.post("/api/register", json={
        "username": "testuser",
        "email": "other@example.com",
        "password": "password123",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    response = await client.post("/api/register", json={
        "username": "otheruser",
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_weak_password(client):
    response = await client.post("/api/register", json={
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "short",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    response = await client.post("/api/login", json={
        "username": "testuser",
        "password": "wrong_password",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_by_email(client, test_user):
    response = await client.post("/api/login", json={
        "email": "test@example.com",
        "password": "wrong_password",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_credentials(client):
    response = await client.post("/api/login", json={
        "password": "password123",
    })
    assert response.status_code == 400
