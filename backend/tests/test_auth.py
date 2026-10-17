"""Tests for authentication and user lifecycle."""

import pytest


@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    # 1. Register new user
    reg_payload = {
        "email": "test.student@university.edu",
        "password": "Password123!",
        "full_name": "Test Student",
    }
    reg_resp = await client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "test.student@university.edu"
    assert "id" in user_data

    # 2. Duplicate registration should fail
    dup_resp = await client.post("/api/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400

    # 3. Login with correct credentials
    login_data = {"username": "test.student@university.edu", "password": "Password123!"}
    login_resp = await client.post("/api/auth/login", data=login_data)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Access protected /me route
    me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test.student@university.edu"

    # 5. Invalid password login
    bad_login = await client.post(
        "/api/auth/login",
        data={"username": "test.student@university.edu", "password": "WrongPassword"},
    )
    assert bad_login.status_code == 401
