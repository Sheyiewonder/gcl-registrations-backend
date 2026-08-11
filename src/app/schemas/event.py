from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)


class EventUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )
    is_active: bool | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    is_active: bool
    created_at: datetime

class EventSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str