from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate


class EventService:

    @staticmethod
    def create(db: Session, data: EventCreate) -> Event:
        event = Event(
            title=data.title,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

    @staticmethod
    def get_all(db: Session):
        return (
            db.query(Event)
            .order_by(Event.created_at.desc())
            .all()
        )

    @staticmethod
    def get_active(db: Session):
        return (
            db.query(Event)
            .filter(Event.is_active == True)
            .order_by(Event.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, event_id: int):
        return (
            db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        event: Event,
        data: EventUpdate,
    ):
        event.title = data.title
        event.is_active = data.is_active

        db.commit()
        db.refresh(event)

        return event

    @staticmethod
    def delete(db: Session, event: Event):
        db.delete(event)
        db.commit()