import uuid
from datetime import datetime, date
from pydantic import BaseModel


class ConsultationCreate(BaseModel):
    patient_name: str
    patient_age: int | None = None
    patient_sex: str | None = None
    patient_id: uuid.UUID | None = None


class UploadUrlResponse(BaseModel):
    upload_url: str
    storage_key: str
    consultation_id: uuid.UUID


class ConsultationStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    error_message: str | None


class TranscriptOut(BaseModel):
    raw_text: str
    detected_language: str | None
    processing_time_ms: int | None

    model_config = {"from_attributes": True}


class GeneratedNoteOut(BaseModel):
    id: uuid.UUID
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    missing_information: list
    ai_model: str
    generation_time_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApproveNoteRequest(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    edit_time_seconds: int | None = None
    generated_note_id: uuid.UUID


class ApprovedNoteOut(BaseModel):
    id: uuid.UUID
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    was_edited: bool
    edit_time_seconds: int | None
    fields_edited: list
    approved_at: datetime
    pdf_storage_key: str | None

    model_config = {"from_attributes": True}


class ConsultationOut(BaseModel):
    id: uuid.UUID
    patient_name: str
    patient_age: int | None
    patient_sex: str | None
    consultation_date: date
    status: str
    error_message: str | None
    chief_complaint: str | None
    transcript: TranscriptOut | None
    generated_note: GeneratedNoteOut | None
    approved_note: ApprovedNoteOut | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsultationListItem(BaseModel):
    id: uuid.UUID
    patient_name: str
    patient_age: int | None
    consultation_date: date
    status: str
    chief_complaint: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
