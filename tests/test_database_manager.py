import pytest
from sqlalchemy import select

from app.db.models import User
from app.repositories.pass_repository import MountainPassRepository
from app.schemas.pass_submission import PassSubmissionSchema
from tests.test_mountain_pass_api import build_payload


def build_submission() -> PassSubmissionSchema:
    return PassSubmissionSchema.model_validate(build_payload())


def test_session_scope_commits_successful_transaction(test_database_manager) -> None:
    payload = build_submission()

    with test_database_manager.session_scope() as session:
        repository = MountainPassRepository(session)
        repository.get_or_create_user(payload)

    with test_database_manager.session_scope() as session:
        user = session.scalar(select(User).where(User.email == payload.user.email))
        assert user is not None


def test_session_scope_rolls_back_on_error(test_database_manager) -> None:
    payload = build_submission()

    with pytest.raises(RuntimeError, match="forced failure"):
        with test_database_manager.session_scope() as session:
            repository = MountainPassRepository(session)
            repository.get_or_create_user(payload)
            raise RuntimeError("forced failure")

    with test_database_manager.session_scope() as session:
        user = session.scalar(select(User).where(User.email == payload.user.email))
        assert user is None
