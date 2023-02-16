from fastapi import APIRouter

from app.auth.api import router as auth_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router, prefix="/auth", tags=["auth"])
