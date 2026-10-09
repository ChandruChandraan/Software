"""API routers aggregation."""

from fastapi import APIRouter
from .auth import router as auth_router
from .system import router as system_router
from .trainees import router as trainees_router
from .groups import router as groups_router
from .users import router as users_router
from .weapons import router as weapons_router
from .targets import router as targets_router
from .exercises import router as exercises_router
from .scenarios import router as scenarios_router
from .sessions import router as sessions_router
from .reports import router as reports_router
from .calibration import router as calibration_router
from .tracker import router as tracker_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(trainees_router)
api_router.include_router(groups_router)
api_router.include_router(users_router)
api_router.include_router(weapons_router)
api_router.include_router(targets_router)
api_router.include_router(exercises_router)
api_router.include_router(scenarios_router)
api_router.include_router(sessions_router)
api_router.include_router(reports_router)
api_router.include_router(calibration_router)
api_router.include_router(tracker_router, prefix="/tracker")
api_router.include_router(tracker_router, prefix="/api/tracker")

__all__ = ["api_router"]
