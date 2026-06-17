import uuid
from datetime import datetime
from pydantic import BaseModel


class PatientCreate(BaseModel):
    name: str
    age: int | None = None
    sex: str | None = None
    phone: str | None = None


class PatientUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    sex: str | None = None
    phone: str | None = None


class PatientOut(BaseModel):
    id: uuid.UUID
    name: str
    age: int | None
    sex: str | None
    phone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
