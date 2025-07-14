from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from fastapi_postgres_app.models import Permission


class ErrorResponse(BaseModel):
    error: str = Field(
        ...,
        json_schema_extra={"example": "UniqueViolation"}
    )
    message: str = Field(
        ...,
        json_schema_extra={"example": "Email already exists."}
    )
    code: int = Field(
        ...,
        json_schema_extra={"example": 409}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Structured error response for failed operations"
        }
    )


class ItemBase(BaseModel):
    # forbid unexpected extra fields
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    price: Optional[int] = Field(
        None,
        ge=0,
        json_schema_extra={"example": 42}
    )  # Must be zero or positive; legacy items with null still allowed

    available: Optional[bool] = True  # Optional for tolerance

    email: EmailStr = Field(
        ...,
        json_schema_extra={"example": "user@example.com"}
    )
    special_id: int = Field(
        ...,
        json_schema_extra={"example": 12345}
    )


class ItemCreate(ItemBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Widget X",
                "description": "A fancy widget",
                "price": 42,
                "available": True,
                "email": "user@example.com",
                "special_id": 12345
            }
        }
    )


class Item(ItemBase):
    id: int
    created_at: Optional[datetime] = None  # Handles legacy nulls

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Widget X",
                "description": "A fancy widget",
                "price": 42,
                "available": True,
                "email": "user@example.com",
                "special_id": 12345,
                "created_at": "2025-07-12T12:34:56"
            }
        }
    )


class ItemUpdate(BaseModel):
    # forbid extra fields on update
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = Field(
        None,
        ge=0,
        json_schema_extra={"example": 42}
    )
    available: Optional[bool] = None
    email: Optional[EmailStr] = None
    special_id: Optional[int] = None


class TokenRequest(BaseModel):
    permissions: Permission
    expires_minutes: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    permissions: Permission
    exp: datetime
