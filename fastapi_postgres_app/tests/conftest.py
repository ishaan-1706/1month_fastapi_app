# fastapi_postgres_app/tests/conftest.py

from dotenv import load_dotenv
load_dotenv()

import os
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient
from fastapi_postgres_app.main import app, get_db
from fastapi_postgres_app.database import Base
from fastapi_postgres_app.deps import (
    require_read_only,
    require_read_write,
    require_full_access,
)

@pytest.fixture(scope="session")
def postgres_container():
    """
    Spin up a Postgres container once per test session.
    Export its full DATABASE_URL so our app and fixtures use it.
    """
    with PostgresContainer("postgres:15") as pg:
        pg.start()  # ensure port & host are set

        # Use the helper URL instead of individual attributes
        database_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = database_url

        # Create tables against this new URL
        engine = create_engine(database_url)
        Base.metadata.create_all(bind=engine)

        yield pg  # container stays alive for all tests

@pytest.fixture()
def db_session(postgres_container):
    """
    Provide a SQLAlchemy session bound to our test container.
    Rolls back after each test.
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(autouse=True)
def cleanup_tables(db_session):
    """
    After each test, truncate all tables to avoid state leakage.
    """
    yield
    # Delete all rows from every table in reverse order
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

@pytest.fixture()
def client(db_session):
    """
    Create a TestClient that:
    1) Overrides get_db to use our test-session.
    2) Overrides all auth dependencies to no-ops so endpoints respond as expected.
    """
    # 1) Override DB dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # 2) Neutralize auth so tests don't require tokens
    app.dependency_overrides[require_read_only] = lambda: None
    app.dependency_overrides[require_read_write] = lambda: None
    app.dependency_overrides[require_full_access] = lambda: None

    client = TestClient(app)
    yield client

    # cleanup
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(db_session):
    """
    Create a TestClient that:
    1) Overrides get_db to use our test-session.
    2) Leaves auth dependencies intact, so real 401/403 flows are enforced.
    """
    def override_get_db():
        yield db_session

    # Clear any previous overrides, then only override the DB
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # cleanup
    app.dependency_overrides.clear()
