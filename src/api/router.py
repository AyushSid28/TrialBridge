import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from src.api.dependencies import DBSession, check_rate_limit, verify_api_key
from src.api.routes.agent_routes import router as agent_router
from src.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

router.include_router(
    agent_router,
    prefix=settings.API_V1_PREFIX,
    # Rate limiting runs before API-key verification so abusive clients are
    # throttled even before we do crypto comparisons.
    dependencies=[Depends(check_rate_limit), Depends(verify_api_key)],
)


@router.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    logger.debug("Health check endpoint accessed")
    return {
        "status": "healthy",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/ready")
async def ready_check(session: DBSession) -> dict[str, str]:
    """Confirm the API can reach Postgres. Used by Docker and orchestrator probes."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )
    return {"status": "ready", "database": "connected"}
