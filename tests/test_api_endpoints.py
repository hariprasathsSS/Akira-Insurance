"""API integration tests for health, demo auth, role authorization, and error formats."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.constants import ROLE_ADMIN, ROLE_ADJUSTER, ROLE_CUSTOMER
from app.db.models.user import User
from app.main import app


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_health_live_endpoint():
    """Liveness probe requires no authentication and returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_unauthenticated_request_fails_with_401():
    """Missing X-Demo-User-ID header returns standard 401 AUTH_REQUIRED envelope."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/api/v1/me")
        assert resp.status_code == 401
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTH_REQUIRED"
        assert "request_id" in data["error"]


@pytest.mark.asyncio
async def test_customer_forbidden_from_admin_endpoint(sample_customer_user):
    """Customer role is rejected with 403 FORBIDDEN when accessing admin routes."""
    transport = ASGITransport(app=app)
    with patch("app.api.deps.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_public_id = AsyncMock(return_value=sample_customer_user)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/api/v1/admin/policy-documents",
                headers={"X-Demo-User-ID": "U-101"},
            )
            assert resp.status_code == 403
            data = resp.json()
            assert data["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_adjuster_forbidden_from_claim_creation(sample_adjuster_user):
    """Adjuster role cannot lodge a new claim (customer only)."""
    transport = ASGITransport(app=app)
    with patch("app.api.deps.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_public_id = AsyncMock(return_value=sample_adjuster_user)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/api/v1/claims",
                json={
                    "policy_public_id": "POL-101",
                    "incident_type": "accident",
                    "incident_date": "2026-10-01",
                    "incident_description": "Sample incident description",
                    "requested_amount": "5000.00",
                    "idempotency_key": "unique-test-key-12345",
                },
                headers={"X-Demo-User-ID": "U-900"},
            )
            assert resp.status_code == 403
            data = resp.json()
            assert data["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_authenticated_me_endpoint_success(sample_customer_user):
    """Authenticated customer calling /me returns their public profile."""
    transport = ASGITransport(app=app)
    with patch("app.api.deps.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_public_id = AsyncMock(return_value=sample_customer_user)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get(
                "/api/v1/me",
                headers={"X-Demo-User-ID": "U-101"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["public_id"] == "U-101"
            assert data["name"] == "Rahul Desai"
            assert data["role"] == "customer"


@pytest.mark.asyncio
async def test_validation_error_envelope(sample_customer_user):
    """Unprocessable entity returns 422 with VALIDATION_ERROR code and details."""
    transport = ASGITransport(app=app)
    with patch("app.api.deps.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_public_id = AsyncMock(return_value=sample_customer_user)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/api/v1/claims",
                json={"invalid_payload": True},
                headers={"X-Demo-User-ID": "U-101"},
            )
            assert resp.status_code == 422
            data = resp.json()
            assert "error" in data
            assert data["error"]["code"] == "VALIDATION_ERROR"
