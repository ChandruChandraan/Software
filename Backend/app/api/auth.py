"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..schemas.common import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """User authentication endpoint (mock/basic token generator)."""
    # Basic authentication placeholder for foundation phase
    if payload.username and payload.password:
        return LoginResponse(
            access_token=f"mock-jwt-token-for-{payload.username}",
            token_type="bearer",
            username=payload.username,
            role="instructor",
        )
    raise HTTPException(status_code=400, detail="Invalid credentials provided")
