from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.passes import get_mountain_pass_service
from app.core.database import DatabaseManager
from app.db.base import Base
from app.main import app
from app.services.pass_service import MountainPassService


class TestDatabaseManager(DatabaseManager):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


@pytest.fixture()
def test_database_manager() -> Generator[TestDatabaseManager, None, None]:
    database_manager = TestDatabaseManager("sqlite://")

    @event.listens_for(database_manager._engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(database_manager._engine)
    try:
        yield database_manager
    finally:
        Base.metadata.drop_all(database_manager._engine)


@pytest.fixture()
def client(test_database_manager: TestDatabaseManager) -> Generator[TestClient, None, None]:
    def override_service() -> MountainPassService:
        return MountainPassService(test_database_manager)

    app.dependency_overrides[get_mountain_pass_service] = override_service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def session_factory(test_database_manager: TestDatabaseManager) -> sessionmaker[Session]:
    return test_database_manager._session_factory
