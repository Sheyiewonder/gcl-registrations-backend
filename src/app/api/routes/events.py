from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.dependencies import get_current_admin, require_super_admin
from app.models.admin import Admin
from app.schemas.event import (
    EventCreate,
    EventResponse,
    EventUpdate,
)
from app.services.event_service import EventService
from app.models.event import Event

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


# ---------------------------------------------------------
# PUBLIC
# ---------------------------------------------------------

@router.get(
    "/active",
    response_model=list[EventResponse],
)
def get_active_events(
    db: Session = Depends(get_db),
):
    """
    Public endpoint.

    Used by the registration frontend to retrieve
    currently active events.
    """
    return EventService.get_active(db)


# ---------------------------------------------------------
# AUTHENTICATED ADMIN
# ---------------------------------------------------------

@router.get(
    "/",
    response_model=list[EventResponse],
)
def get_events(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    Retrieve all events.

    Requires an authenticated admin.
    """
    return EventService.get_all(db)


# ---------------------------------------------------------
# SUPER ADMIN
# ---------------------------------------------------------

@router.post(
    "/",
    response_model=EventResponse,
    status_code=201,
)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    """
    Create a new event.

    Super admin only.
    """
    return EventService.create(db, data)


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
)
def update_event(
    event_id: int,
    data: EventUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    event = db.get(Event, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if data.title is not None:
        new_title = data.title.strip()

        duplicate = (
            db.query(Event)
            .filter(
                Event.title == new_title,
                Event.id != event_id,
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An event with this title already exists",
            )

        event.title = new_title

    if data.is_active is not None:
        event.is_active = data.is_active

    db.commit()
    db.refresh(event)

    return event


@router.delete(
    "/{event_id}",
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_super_admin),
):
    """
    Delete an event.

    Super admin only.
    """
    event = EventService.get_by_id(
        db,
        event_id,
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    EventService.delete(
        db,
        event,
    )

    return {
        "message": "Event deleted successfully"
    }