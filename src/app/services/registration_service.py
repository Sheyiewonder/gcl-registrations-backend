from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.registration import Registration
from app.models.event import Event
from app.schemas.registration import RegistrationCreate

from app.core.exceptions import (
    EventNotFoundError,
    EventInactiveError,
)

from datetime import datetime

class RegistrationService:

    @staticmethod
    def create(
        db: Session,
        data: RegistrationCreate,
    ) -> Registration:

        event = (
            db.query(Event)
            .filter(Event.id == data.event_id)
            .first()
        )

        if event is None:
            raise EventNotFoundError()

        if not event.is_active:
            raise EventInactiveError()

        registration = Registration(
            event_id=data.event_id,

            first_name=data.first_name,
            last_name=data.last_name,

            gender=data.gender,

            phone=data.phone,
            email=data.email,

            country=data.country,
            state=data.state,
            city=data.city,

            denomination=data.denomination,
            other_denomination=data.other_denomination,

            accommodation=data.accommodation,
        )

        db.add(registration)
        db.commit()
        db.refresh(registration)

        registration.event = event

        return registration

    @staticmethod
    def get_all(
        db: Session,
        event_id: int | None = None,
        search: str | None = None,
        gender: str | None = None,
        denomination: str | None = None,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
        accommodation: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        query = (
            db.query(Registration)
            .options(joinedload(Registration.event))
        )

        if event_id is not None:
            query = query.filter(
                Registration.event_id == event_id
            )

        if search:
            search_term = f"%{search.strip()}%"

            query = query.filter(
                or_(
                    Registration.first_name.ilike(search_term),
                    Registration.last_name.ilike(search_term),
                    Registration.phone.ilike(search_term),
                    Registration.email.ilike(search_term),
                )
            )

        if gender:
            query = query.filter(
                Registration.gender == gender
            )

        if denomination:
            query = query.filter(
                Registration.denomination == denomination
            )

        if country:
            query = query.filter(
                Registration.country == country
            )

        if state:
            query = query.filter(
                Registration.state == state
            )

        if city:
            query = query.filter(
                Registration.city == city
            )

        if accommodation is not None:
            query = query.filter(
                Registration.accommodation == accommodation
            )

        if date_from:
            query = query.filter(
                Registration.created_at >= date_from
            )

        if date_to:
            query = query.filter(
                Registration.created_at <= date_to
            )

        return (
            query
            .order_by(Registration.created_at.desc())
            .all()
    )

    @staticmethod
    def get_by_id(
        db: Session,
        registration_id: int,
    ):
        return (
            db.query(Registration)
            .options(joinedload(Registration.event))
            .filter(Registration.id == registration_id)
            .first()
        )

    @staticmethod
    def get_stats(
        db: Session,
    ):
        total = db.query(Registration).count()

        return {
            "total_registrations": total,
        }
