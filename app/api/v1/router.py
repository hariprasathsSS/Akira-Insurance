"""API v1 root router aggregating all domain subrouters."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.adjuster import router as adjuster_router
from app.api.v1.admin_documents import router as admin_documents_router
from app.api.v1.admin_jobs import router as admin_jobs_router
from app.api.v1.admin_metrics import router as admin_metrics_router
from app.api.v1.billing import router as billing_router
from app.api.v1.chat import router as chat_router
from app.api.v1.claims import router as claims_router
from app.api.v1.demo_auth import router as demo_auth_router
from app.api.v1.me import router as me_router
from app.api.v1.policies import router as policies_router

api_v1_router = APIRouter()

# Current user & demo auth
api_v1_router.include_router(me_router)
api_v1_router.include_router(demo_auth_router)

# Customer domain
api_v1_router.include_router(policies_router)
api_v1_router.include_router(billing_router)
api_v1_router.include_router(claims_router)
api_v1_router.include_router(chat_router)

# Adjuster domain
api_v1_router.include_router(adjuster_router)

# Admin domain
api_v1_router.include_router(admin_documents_router)
api_v1_router.include_router(admin_jobs_router)
api_v1_router.include_router(admin_metrics_router)
