# fastapi_postgres_app/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_postgres_app.jwt_utils import verify_access_token
from fastapi_postgres_app.schemas import TokenData
from fastapi_postgres_app.models import Permission

# Don’t auto-error so we can return a 401 for missing tokens
bearer_scheme = HTTPBearer(auto_error=False)

def get_token_data(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TokenData:
    # 401 if no Authorization header
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    # 401 if token invalid or expired
    try:
        return verify_access_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_read_only(td: TokenData = Depends(get_token_data)):
    if td.permissions != Permission.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read-only access required"
        )
    return td


def require_read_write(td: TokenData = Depends(get_token_data)):
    if td.permissions not in {Permission.read_write, Permission.full_access}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read/write access required"
        )
    return td


def require_full_access(td: TokenData = Depends(get_token_data)):
    if td.permissions != Permission.full_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full access required"
        )
    return td
