from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.dependencies import get_current_admin

from app.models.admin import Admin

from app.schemas.registration import (
    RegistrationCreate,
    RegistrationResponse,
)

from app.core.exceptions import (
    EventInactiveError,
    EventNotFoundError,
)

from app.services.registration_service import (
    RegistrationService,
)

from app.services.registration_export_service import (
    RegistrationExportService,
)

router = APIRouter(
    prefix="/registrations",
    tags=["Registrations"],
)


# --------------------------------------------------
# PUBLIC REGISTRATION
# --------------------------------------------------

@router.post(
    "/",
    response_model=RegistrationResponse,
)
def create_registration(
    data: RegistrationCreate,
    db: Session = Depends(get_db),
):
    try:
        return RegistrationService.create(
            db,
            data,
        )

    except EventNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Selected event was not found.",
        )

    except EventInactiveError:
        raise HTTPException(
            status_code=400,
            detail="This event is no longer accepting registrations.",
        )


# --------------------------------------------------
# ADMIN: LIST REGISTRATIONS
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[RegistrationResponse],
)
def get_registrations(
    event_id: int | None = Query(default=None),
    search: str | None = Query(default=None),

    gender: str | None = Query(default=None),
    denomination: str | None = Query(default=None),
    country: str | None = Query(default=None),
    state: str | None = Query(default=None),
    city: str | None = Query(default=None),
    accommodation: bool | None = Query(default=None),

    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),

    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return RegistrationService.get_all(
        db=db,
        event_id=event_id,
        search=search,
        gender=gender,
        denomination=denomination,
        country=country,
        state=state,
        city=city,
        accommodation=accommodation,
        date_from=date_from,
        date_to=date_to,
    )
# --------------------------------------------------
# ADMIN: GET SINGLE REGISTRATION
# --------------------------------------------------

@router.get(
    "/{registration_id}",
    response_model=RegistrationResponse,
)
def get_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    registration = RegistrationService.get_by_id(
        db,
        registration_id,
    )

    if not registration:
        raise HTTPException(
            status_code=404,
            detail="Registration not found",
        )

    return registration


# --------------------------------------------------
# ADMIN: REGISTRATION STATS
# --------------------------------------------------

@router.get(
    "/stats/summary",
)
def get_registration_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return RegistrationService.get_stats(db)

@router.get(
    "/export/excel",
)
def export_registrations_excel(
    event_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    denomination: str | None = Query(default=None),
    country: str | None = Query(default=None),
    state: str | None = Query(default=None),
    city: str | None = Query(default=None),
    accommodation: bool | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),

    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    registrations = RegistrationService.get_all(
        db=db,
        event_id=event_id,
        search=search,
        gender=gender,
        denomination=denomination,
        country=country,
        state=state,
        city=city,
        accommodation=accommodation,
        date_from=date_from,
        date_to=date_to,
    )

    file = RegistrationExportService.to_excel(
        registrations
    )

    return StreamingResponse(
        file,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="registrations.xlsx"'
            )
        },
    )

@router.get(
    "/export/pdf",
)
def export_registrations_pdf(
    event_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    denomination: str | None = Query(default=None),
    country: str | None = Query(default=None),
    state: str | None = Query(default=None),
    city: str | None = Query(default=None),
    accommodation: bool | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),

    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    registrations = RegistrationService.get_all(
        db=db,
        event_id=event_id,
        search=search,
        gender=gender,
        denomination=denomination,
        country=country,
        state=state,
        city=city,
        accommodation=accommodation,
        date_from=date_from,
        date_to=date_to,
    )

    file = RegistrationExportService.to_pdf(
        registrations
    )

    return StreamingResponse(
        file,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="registrations.pdf"'
            )
        },
    )