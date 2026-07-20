"""Root API router composition for the RIFTLESS backend."""

from fastapi import APIRouter

from app.api.routes import changes, health, risk, runs

api_router = APIRouter()
api_router.include_router(health.router)
# F5.x operations — fixed API path prefix (not a general versioning system).
api_router.include_router(changes.router, prefix="/api/v1")
api_router.include_router(risk.router, prefix="/api/v1")
api_router.include_router(runs.router, prefix="/api/v1")
