from dotenv import load_dotenv
load_dotenv()


import os
import jwt
from datetime import datetime, timedelta, timezone
from jwt import PyJWTError
from fastapi import HTTPException, status
from fastapi_postgres_app.schemas import TokenData

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM  = os.getenv("JWT_ALGORITHM")

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
