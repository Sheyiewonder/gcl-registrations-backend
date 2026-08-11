from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    gender: Mapped[str] = mapped_column(String(20))

    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))

    denomination: Mapped[str] = mapped_column(String(150))
    other_denomination: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    accommodation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    event = relationship("Event")