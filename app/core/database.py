from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.exceptions import DatabaseConnectionError, PersistenceError


class DatabaseManager:
    """Centralized database engine and session management."""

    def __init__(self) -> None:
        settings = get_settings()
        self._engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
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
        except OperationalError as exc:
            session.rollback()
            raise DatabaseConnectionError() from exc
        except SQLAlchemyError as exc:
            session.rollback()
            raise PersistenceError() from exc
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
        except OperationalError as exc:
            raise DatabaseConnectionError() from exc
        finally:
            session.close()


database_manager = DatabaseManager()
