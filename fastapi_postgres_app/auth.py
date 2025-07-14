from datetime import timedelta
from fastapi import APIRouter, HTTPException
from fastapi_postgres_app.schemas import TokenRequest, TokenResponse
from fastapi_postgres_app.jwt_utils import create_access_token

router = APIRouter(prefix="/token", tags=["auth"])

@router.post("/", response_model=TokenResponse)
def generate_token(req: TokenRequest):
    if req.expires_minutes <= 0:
        raise HTTPException(400, "expires_minutes must be positive")
    data = {"permissions": req.permissions.value}
    token = create_access_token(
        data=data,
        expires_delta=timedelta(minutes=req.expires_minutes)
    )
    return {"access_token": token}
