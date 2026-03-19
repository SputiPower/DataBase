from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models import MountainPass, PassCoordinate, PassImage, PassLevel, User
from app.schemas.pass_submission import ImageSchema, PassSubmissionSchema


class MountainPassRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_user(self, payload: PassSubmissionSchema) -> User:
        user = self.session.scalar(select(User).where(User.email == payload.user.email))
        if user:
            user.first_name = payload.user.name
            user.last_name = payload.user.fam
            user.middle_name = payload.user.otc
            user.phone = payload.user.phone
            self.session.flush()
            return user

        user = User(
            email=payload.user.email,
            first_name=payload.user.name,
            last_name=payload.user.fam,
            middle_name=payload.user.otc,
            phone=payload.user.phone,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def create_pass(self, payload: PassSubmissionSchema, user_id: int) -> MountainPass:
        mountain_pass = MountainPass(
            beauty_title=payload.beauty_title,
            title=payload.title,
            other_titles=payload.other_titles,
            connect=payload.connect,
            add_time=payload.add_time,
            user_id=user_id,
        )
        self.session.add(mountain_pass)
        self.session.flush()
        return mountain_pass

    def create_coordinates(self, payload: PassSubmissionSchema, mountain_pass_id: int) -> PassCoordinate:
        coordinates = PassCoordinate(
            mountain_pass_id=mountain_pass_id,
            latitude=payload.coords.latitude,
            longitude=payload.coords.longitude,
            height=payload.coords.height,
        )
        self.session.add(coordinates)
        self.session.flush()
        return coordinates

    def create_levels(self, payload: PassSubmissionSchema, mountain_pass_id: int) -> PassLevel:
        levels = PassLevel(
            mountain_pass_id=mountain_pass_id,
            winter=payload.level.winter,
            spring=payload.level.spring,
            summer=payload.level.summer,
            autumn=payload.level.autumn,
        )
        self.session.add(levels)
        self.session.flush()
        return levels

    def create_images(self, payload: PassSubmissionSchema, mountain_pass_id: int) -> list[PassImage]:
        images = self._build_image_entities(payload.images)
        for image in images:
            image.mountain_pass_id = mountain_pass_id
            self.session.add(image)

        self.session.flush()
        return images

    def get_pereval_by_id(self, mountain_pass_id: int) -> MountainPass | None:
        statement = (
            select(MountainPass)
            .where(MountainPass.id == mountain_pass_id)
            .options(
                joinedload(MountainPass.user),
                joinedload(MountainPass.coordinates),
                joinedload(MountainPass.levels),
                selectinload(MountainPass.images),
            )
        )
        return self.session.scalar(statement)

    def get_perevals_by_user_email(self, email: str) -> Sequence[MountainPass]:
        statement = (
            select(MountainPass)
            .join(MountainPass.user)
            .where(User.email == email)
            .order_by(MountainPass.created_at.desc(), MountainPass.id.desc())
        )
        return list(self.session.scalars(statement))

    def update_pereval_if_new(self, mountain_pass: MountainPass, payload: PassSubmissionSchema) -> MountainPass:
        mountain_pass.beauty_title = payload.beauty_title
        mountain_pass.title = payload.title
        mountain_pass.other_titles = payload.other_titles
        mountain_pass.connect = payload.connect
        mountain_pass.add_time = payload.add_time

        if mountain_pass.coordinates is None:
            mountain_pass.coordinates = PassCoordinate(
                latitude=payload.coords.latitude,
                longitude=payload.coords.longitude,
                height=payload.coords.height,
            )
        else:
            mountain_pass.coordinates.latitude = payload.coords.latitude
            mountain_pass.coordinates.longitude = payload.coords.longitude
            mountain_pass.coordinates.height = payload.coords.height

        if mountain_pass.levels is None:
            mountain_pass.levels = PassLevel(
                winter=payload.level.winter,
                spring=payload.level.spring,
                summer=payload.level.summer,
                autumn=payload.level.autumn,
            )
        else:
            mountain_pass.levels.winter = payload.level.winter
            mountain_pass.levels.spring = payload.level.spring
            mountain_pass.levels.summer = payload.level.summer
            mountain_pass.levels.autumn = payload.level.autumn

        mountain_pass.images.clear()
        self.session.flush()
        mountain_pass.images.extend(self._build_image_entities(payload.images))
        self.session.flush()
        return mountain_pass

    @staticmethod
    def _build_image_entities(images: Sequence[ImageSchema]) -> list[PassImage]:
        entities: list[PassImage] = []
        for position, image in enumerate(images):
            entities.append(
                PassImage(
                    title=image.title,
                    image_data=image.decoded_bytes,
                    content_type=image.content_type,
                    position=position,
                )
            )
        return entities
