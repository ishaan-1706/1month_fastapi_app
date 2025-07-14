from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from fastapi_postgres_app.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Integer)
    available = Column(Boolean, default=True)

    # Use Postgres to generate a UTC timestamp with timezone
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    email      = Column(String, unique=True, nullable=False)
    special_id = Column(Integer, unique=True, nullable=False)


class Permission(str, Enum):
    read_only   = "read_only"
    read_write  = "read_write"
    full_access = "full_access"
