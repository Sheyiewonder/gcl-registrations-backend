from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.event import EventSummary

class RegistrationCreate(BaseModel):
    event_id: int

    first_name: str
    last_name: str

    gender: str

    phone: str
    email: str | None = None

    country: str
    state: str
    city: str

    denomination: str
    other_denomination: str | None = None

    accommodation: bool


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    event: EventSummary | None = None

    first_name: str
    last_name: str

    gender: str

    phone: str
    email: str | None

    country: str
    state: str
    city: str

    denomination: str
    other_denomination: str | None

    accommodation: bool

    created_at: datetime

# class RegistrationAdminResponse(RegistrationResponse):
#     event_title: str