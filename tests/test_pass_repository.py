from app.db.enums import PassStatus
from app.db.models import MountainPass, PassCoordinate, PassImage, PassLevel, User
from app.repositories.pass_repository import MountainPassRepository
from app.schemas.pass_submission import PassSubmissionSchema
from tests.test_mountain_pass_api import build_payload


def build_submission() -> PassSubmissionSchema:
    return PassSubmissionSchema.model_validate(build_payload())


def test_repository_creates_user_and_related_pass_entities(session_factory) -> None:
    payload = build_submission()

    with session_factory() as session:
        repository = MountainPassRepository(session)

        user = repository.get_or_create_user(payload)
        mountain_pass = repository.create_pass(payload, user.id)
        coordinates = repository.create_coordinates(payload, mountain_pass.id)
        levels = repository.create_levels(payload, mountain_pass.id)
        images = repository.create_images(payload, mountain_pass.id)
        session.commit()

    with session_factory() as session:
        persisted_user = session.get(User, user.id)
        persisted_pass = session.get(MountainPass, mountain_pass.id)
        persisted_coordinates = session.get(PassCoordinate, coordinates.id)
        persisted_levels = session.get(PassLevel, levels.id)
        persisted_images = (
            session.query(PassImage)
            .filter(PassImage.mountain_pass_id == mountain_pass.id)
            .order_by(PassImage.position.asc())
            .all()
        )

        assert persisted_user is not None
        assert persisted_user.email == payload.user.email
        assert persisted_pass is not None
        assert persisted_pass.status == PassStatus.NEW
        assert persisted_coordinates is not None
        assert persisted_coordinates.height == payload.coords.height
        assert persisted_levels is not None
        assert persisted_levels.summer == payload.level.summer
        assert len(persisted_images) == 2
        assert [image.title for image in persisted_images] == ["Седловина", "Подъём"]


def test_repository_reuses_existing_user_and_updates_profile(session_factory) -> None:
    original_payload = build_submission()
    updated_payload = build_submission()
    updated_payload.user.phone = "+7 999 11 22"
    updated_payload.user.name = "Пётр"

    with session_factory() as session:
        repository = MountainPassRepository(session)
        original_user = repository.get_or_create_user(original_payload)
        session.commit()

    with session_factory() as session:
        repository = MountainPassRepository(session)
        updated_user = repository.get_or_create_user(updated_payload)
        session.commit()

        assert updated_user.id == original_user.id
        assert updated_user.phone == updated_payload.user.phone
        assert updated_user.first_name == updated_payload.user.name


def test_repository_updates_existing_pass_payload(session_factory) -> None:
    payload = build_submission()

    with session_factory() as session:
        repository = MountainPassRepository(session)
        user = repository.get_or_create_user(payload)
        mountain_pass = repository.create_pass(payload, user.id)
        repository.create_coordinates(payload, mountain_pass.id)
        repository.create_levels(payload, mountain_pass.id)
        repository.create_images(payload, mountain_pass.id)
        session.commit()
        mountain_pass_id = mountain_pass.id

    updated_payload = build_submission()
    updated_payload.title = "Пхия 2"
    updated_payload.coords.height = 1500
    updated_payload.level.winter = "2А"
    updated_payload.images = updated_payload.images[:1]
    updated_payload.images[0].title = "Обновлённое фото"

    with session_factory() as session:
        repository = MountainPassRepository(session)
        mountain_pass = repository.get_pereval_by_id(mountain_pass_id)

        assert mountain_pass is not None

        repository.update_pereval_if_new(mountain_pass, updated_payload)
        session.commit()

    with session_factory() as session:
        persisted_pass = session.get(MountainPass, mountain_pass_id)
        persisted_images = (
            session.query(PassImage)
            .filter(PassImage.mountain_pass_id == mountain_pass_id)
            .order_by(PassImage.position.asc())
            .all()
        )

        assert persisted_pass is not None
        assert persisted_pass.title == "Пхия 2"
        assert persisted_pass.coordinates.height == 1500
        assert persisted_pass.levels.winter == "2А"
        assert len(persisted_images) == 1
        assert persisted_images[0].title == "Обновлённое фото"
