"""Pytest fixtures for AKIRA INSURANCE test suite."""
from __future__ import annotations

import os
import sys
import uuid
from decimal import Decimal
from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure root workspace directory is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Set testing environment variables before importing app
os.environ["APP_ENV"] = "development"
os.environ["DEMO_AUTH_ENABLED"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.api.deps import get_current_user, get_db
from app.core.constants import ROLE_ADMIN, ROLE_ADJUSTER, ROLE_CUSTOMER
from app.db.models.user import User
from app.main import app


@pytest.fixture
def sample_customer_user() -> User:
    return User(
        id=uuid.uuid4(),
        public_id="U-101",
        name="Rahul Desai",
        email="rahul.desai@example.test",
        role=ROLE_CUSTOMER,
        is_active=True,
    )


@pytest.fixture
def other_customer_user() -> User:
    return User(
        id=uuid.uuid4(),
        public_id="U-102",
        name="Priya Sharma",
        email="priya.sharma@example.test",
        role=ROLE_CUSTOMER,
        is_active=True,
    )


@pytest.fixture
def sample_adjuster_user() -> User:
    return User(
        id=uuid.uuid4(),
        public_id="U-900",
        name="Vikram Singh",
        email="vikram.singh@example.test",
        role=ROLE_ADJUSTER,
        is_active=True,
    )


@pytest.fixture
def sample_admin_user() -> User:
    return User(
        id=uuid.uuid4(),
        public_id="U-901",
        name="Akira Admin",
        email="admin@akira.example.test",
        role=ROLE_ADMIN,
        is_active=True,
    )


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Test client using ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
