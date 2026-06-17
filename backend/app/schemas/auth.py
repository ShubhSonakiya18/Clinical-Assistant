import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    clinic_name: str | None = None
    specialization: str = "Orthopedics"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DoctorOut(BaseModel):
    id: uuid.UUID
    specialization: str
    clinic_name: str | None
    preferred_language: str
    subscription_tier: str
    consultations_this_month: int
    free_quota: int

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserOut
    doctor: DoctorOut
