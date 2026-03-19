from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import PassStatus


bigint_type = BigInteger().with_variant(Integer, "sqlite")

pass_status_enum = Enum(
    PassStatus,
    name="mountain_pass_status",
    values_callable=lambda enum_type: [member.value for member in enum_type],
)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 3", name="email_not_blank"),
        CheckConstraint("length(trim(first_name)) > 0", name="first_name_not_blank"),
        CheckConstraint("length(trim(last_name)) > 0", name="last_name_not_blank"),
        CheckConstraint("length(trim(phone)) > 0", name="phone_not_blank"),
    )

    id: Mapped[int] = mapped_column(bigint_type, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mountain_passes: Mapped[list["MountainPass"]] = relationship(back_populates="user")


class MountainPass(Base):
    __tablename__ = "mountain_passes"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="title_not_blank"),
        Index("ix_mountain_passes_status", "status"),
        Index("ix_mountain_passes_add_time", "add_time"),
        Index("ix_mountain_passes_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(bigint_type, primary_key=True)
    beauty_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    other_titles: Mapped[str | None] = mapped_column(String(255), nullable=True)
    connect: Mapped[str | None] = mapped_column(Text, nullable=True)
    add_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    status: Mapped[PassStatus] = mapped_column(
        pass_status_enum,
        nullable=False,
        default=PassStatus.NEW,
        server_default=PassStatus.NEW.value,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="mountain_passes")
    coordinates: Mapped["PassCoordinate"] = relationship(
        back_populates="mountain_pass",
        cascade="all, delete-orphan",
        uselist=False,
    )
    levels: Mapped["PassLevel"] = relationship(
        back_populates="mountain_pass",
        cascade="all, delete-orphan",
        uselist=False,
    )
    images: Mapped[list["PassImage"]] = relationship(
        back_populates="mountain_pass",
        cascade="all, delete-orphan",
        order_by="PassImage.position",
    )


class PassCoordinate(Base):
    __tablename__ = "pass_coordinates"
    __table_args__ = (
        UniqueConstraint("mountain_pass_id", name="uq_pass_coordinates_mountain_pass_id"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="chk_pass_coordinates_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="chk_pass_coordinates_longitude"),
        CheckConstraint("height >= 0", name="chk_pass_coordinates_height"),
    )

    id: Mapped[int] = mapped_column(bigint_type, primary_key=True)
    mountain_pass_id: Mapped[int] = mapped_column(
        ForeignKey("mountain_passes.id", ondelete="CASCADE"),
        nullable=False,
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(8, 5), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(8, 5), nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    mountain_pass: Mapped["MountainPass"] = relationship(back_populates="coordinates")


class PassLevel(Base):
    __tablename__ = "pass_levels"
    __table_args__ = (
        UniqueConstraint("mountain_pass_id", name="uq_pass_levels_mountain_pass_id"),
    )

    id: Mapped[int] = mapped_column(bigint_type, primary_key=True)
    mountain_pass_id: Mapped[int] = mapped_column(
        ForeignKey("mountain_passes.id", ondelete="CASCADE"),
        nullable=False,
    )
    winter: Mapped[str | None] = mapped_column(String(16), nullable=True)
    spring: Mapped[str | None] = mapped_column(String(16), nullable=True)
    summer: Mapped[str | None] = mapped_column(String(16), nullable=True)
    autumn: Mapped[str | None] = mapped_column(String(16), nullable=True)

    mountain_pass: Mapped["MountainPass"] = relationship(back_populates="levels")


class PassImage(Base):
    __tablename__ = "pass_images"
    __table_args__ = (
        Index("ix_pass_images_mountain_pass_id", "mountain_pass_id"),
        CheckConstraint("position >= 0", name="chk_pass_images_position"),
        UniqueConstraint("mountain_pass_id", "position", name="uq_pass_images_mountain_pass_position"),
    )

    id: Mapped[int] = mapped_column(bigint_type, primary_key=True)
    mountain_pass_id: Mapped[int] = mapped_column(
        ForeignKey("mountain_passes.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    position: Mapped[int] = mapped_column(bigint_type, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mountain_pass: Mapped["MountainPass"] = relationship(back_populates="images")
