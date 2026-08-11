from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class AdminCreate(BaseModel):
    email: EmailStr
    role: str = "admin"


class AdminResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminStatusUpdate(BaseModel):
    is_active: bool


class AdminRoleUpdate(BaseModel):
    role: str