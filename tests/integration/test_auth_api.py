"""Integration tests for authentication endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAuthRegister:
    async def test_register_physician(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "email": "newdoc@hospital.com",
            "password": "SecurePass123!",
            "full_name": "Dr. New Doctor",
            "role": "physician",
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "duplicate@hospital.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Duplicate",
            "role": "physician",
        }
        await client.post("/auth/register", json=payload)
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 409  # ConflictError

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "SecurePass123!",
            "full_name": "Bad Email",
            "role": "physician",
        })
        assert resp.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "email": "weakpass@hospital.com",
            "password": "123",
            "full_name": "Dr. Weak",
            "role": "physician",
        })
        assert resp.status_code == 422


@pytest.mark.integration
class TestAuthLogin:
    async def test_login_with_valid_credentials(self, client: AsyncClient):
        # Register first
        await client.post("/auth/register", json={
            "email": "logintest@hospital.com",
            "password": "SecurePass123!",
            "full_name": "Dr. Login Test",
            "role": "physician",
        })
        # Then login via OAuth2 form
        resp = await client.post("/auth/token", data={
            "username": "logintest@hospital.com",
            "password": "SecurePass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        resp = await client.post("/auth/token", data={
            "username": "logintest@hospital.com",
            "password": "WrongPassword!",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/auth/token", data={
            "username": "ghost@hospital.com",
            "password": "AnyPassword123!",
        })
        assert resp.status_code == 401


@pytest.mark.integration
class TestAuthMe:
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert "role" in data

    async def test_get_current_user_no_token(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        resp = await client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401
