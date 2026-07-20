"""FastAPI application factory for the RIFTLESS backend foundation.

Creating the application must remain free of network calls, database
connections, secret-provider access, AI provider calls, filesystem
mutation, and background workers.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the RIFTLESS FastAPI application.

    Parameters
    ----------
    settings:
        Optional pre-built settings instance. When omitted, settings are
        loaded via ``get_settings()``.
    """
    resolved = settings if settings is not None else get_settings()

    application = FastAPI(
        title="RIFTLESS API",
        description="Backend control-plane foundation for RIFTLESS.",
        version=resolved.app_version,
        debug=resolved.debug,
    )

    application.state.settings = resolved
    register_exception_handlers(application)
    application.include_router(api_router, prefix=resolved.api_prefix)

    return application


# Single importable application instance (ASGI entrypoint).
app = create_app()
