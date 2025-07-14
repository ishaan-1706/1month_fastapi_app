from dotenv import load_dotenv
load_dotenv()

from fastapi import Request, FastAPI, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from fastapi_postgres_app import models, schemas
from fastapi_postgres_app.database import engine, SessionLocal
from fastapi_postgres_app.auth import router as auth_router
from fastapi_postgres_app.deps import (
    require_read_only,
    require_read_write,
    require_full_access,
)

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# Mount the token-generation endpoint
app.include_router(auth_router)


# Dependency for getting a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post(
    "/items/",
    response_model=schemas.Item,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_read_write)],
    responses={
        201: {
            "description": "Item created",
            "headers": {
                "Location": {
                    "description": "URL of the new item",
                    "schema": {"type": "string", "example": "/items/1"}
                }
            }
        },
        409: {
            "model": schemas.ErrorResponse,
            "description": "Conflict – unique constraint violation"
        },
        422: {
            "description": "Validation Error"
        },
    }
)
def create_item(
    item: schemas.ItemCreate,
    response: Response,
    db: Session = Depends(get_db)
):
    db_item = models.Item(**item.model_dump())
    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "UniqueViolation",
                "message": "Email or special_id already exists.",
                "code": 409
            }
        )
    response.headers["Location"] = f"/items/{db_item.id}"
    return db_item


@app.get(
    "/items/",
    response_model=List[schemas.Item],
    dependencies=[Depends(require_read_only)],
    responses={
        422: {
            "description": "Validation Error"
        }
    }
)
def read_items(
    available: Optional[bool] = Query(None),
    price_lt: Optional[int] = Query(None),
    price_gt: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Item)
    if available is not None:
        query = query.filter(models.Item.available == available)
    if price_lt is not None:
        query = query.filter(models.Item.price < price_lt)
    if price_gt is not None:
        query = query.filter(models.Item.price > price_gt)
    if search:
        term = f"%{search}%"
        query = query.filter(
            models.Item.name.ilike(term) |
            models.Item.description.ilike(term)
        )
    return query.all()


@app.get(
    "/items/{item_id}",
    response_model=schemas.Item,
    dependencies=[Depends(require_read_only)],
    responses={
        404: {
            "model": schemas.ErrorResponse,
            "description": "Item not found"
        },
        422: {
            "description": "Validation Error"
        }
    }
)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Item {item_id} not found.",
                "code": 404
            }
        )
    return item


@app.put(
    "/items/{item_id}",
    response_model=schemas.Item,
    dependencies=[Depends(require_read_write)],
    responses={
        404: {
            "model": schemas.ErrorResponse,
            "description": "Item not found"
        },
        409: {
            "model": schemas.ErrorResponse,
            "description": "Conflict – unique constraint violation"
        },
        422: {
            "description": "Validation Error"
        }
    }
)
def update_item(
    item_id: int,
    updated_item: schemas.ItemCreate,
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Item {item_id} not found.",
                "code": 404
            }
        )

    for key, value in updated_item.model_dump().items():
        setattr(item, key, value)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "UniqueViolation",
                "message": "Email or special_id already exists.",
                "code": 409
            }
        )
    return item


@app.patch(
    "/items/{item_id}",
    response_model=schemas.Item,
    dependencies=[Depends(require_read_write)],
    responses={
        404: {
            "model": schemas.ErrorResponse,
            "description": "Item not found"
        },
        409: {
            "model": schemas.ErrorResponse,
            "description": "Conflict – unique constraint violation"
        },
        422: {
            "description": "Validation Error"
        }
    }
)
def partial_update_item(
    item_id: int,
    updates: schemas.ItemUpdate,
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Item {item_id} not found.",
                "code": 404
            }
        )

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "UniqueViolation",
                "message": "Email or special_id already exists.",
                "code": 409
            }
        )
    return item


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_full_access)],
    responses={
        404: {
            "model": schemas.ErrorResponse,
            "description": "Item not found"
        }
    }
)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Item {item_id} not found.",
                "code": 404
            }
        )
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # If detail is a dict, return it as the root JSON; else fall back to {"detail": ...}
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
