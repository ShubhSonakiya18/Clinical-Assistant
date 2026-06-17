import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.consultation import Consultation
from app.models.audio_file import AudioFile
from app.models.generated_note import GeneratedNote
from app.models.approved_note import ApprovedNote
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.consultation import (
    ConsultationCreate, ConsultationOut, ConsultationListItem,
    UploadUrlResponse, ConsultationStatusResponse,
    ApproveNoteRequest, ApprovedNoteOut,
    TranscriptOut, GeneratedNoteOut,
)
from app.services.audio_service import generate_upload_url, upload_bytes
from app.services.pdf_service import generate_pdf
from app.tasks.process_consultation import process_consultation_pipeline
from app.routers.auth import get_current_doctor, get_current_user
from app.config import settings

router = APIRouter(prefix="/consultations", tags=["consultations"])


# ── helpers ─────────────────────────────────────────────────────────────────

def _get_owned(consultation_id: uuid.UUID, doctor: Doctor, db: Session) -> Consultation:
    c = db.query(Consultation).filter(
        Consultation.id == consultation_id,
        Consultation.doctor_id == doctor.id,
        Consultation.is_deleted == False,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return c


def _to_out(c: Consultation) -> ConsultationOut:
    transcript_out = TranscriptOut.model_validate(c.transcript) if c.transcript else None
    generated_note_out = (
        GeneratedNoteOut.model_validate(c.generated_notes[0])
        if c.generated_notes
        else None
    )
    approved_note_out = ApprovedNoteOut.model_validate(c.approved_note) if c.approved_note else None
    return ConsultationOut(
        id=c.id,
        patient_name=c.patient_name,
        patient_age=c.patient_age,
        patient_sex=c.patient_sex,
        consultation_date=c.consultation_date,
        status=c.status,
        error_message=c.error_message,
        chief_complaint=c.chief_complaint,
        transcript=transcript_out,
        generated_note=generated_note_out,
        approved_note=approved_note_out,
        created_at=c.created_at,
    )


# ── routes ───────────────────────────────────────────────────────────────────

@router.post("", response_model=ConsultationOut, status_code=201)
def create_consultation(
    body: ConsultationCreate,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    if doctor.subscription_tier == "free" and doctor.consultations_this_month >= doctor.free_quota:
        raise HTTPException(
            status_code=402,
            detail="Free quota exhausted. Please upgrade to Pro.",
        )
    c = Consultation(
        doctor_id=doctor.id,
        patient_id=body.patient_id,
        patient_name=body.patient_name,
        patient_age=body.patient_age,
        patient_sex=body.patient_sex,
        status="created",
    )
    db.add(c)
    doctor.consultations_this_month += 1
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.post("/{consultation_id}/upload-url", response_model=UploadUrlResponse)
def get_upload_url(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = _get_owned(consultation_id, doctor, db)
    storage_key = f"audio/{doctor.id}/{consultation_id}/recording.webm"
    upload_url = generate_upload_url(storage_key)

    audio_file = db.query(AudioFile).filter(AudioFile.consultation_id == consultation_id).first()
    if not audio_file:
        audio_file = AudioFile(
            consultation_id=consultation_id,
            storage_key=storage_key,
            storage_bucket=settings.R2_BUCKET_NAME,
        )
        db.add(audio_file)
    else:
        audio_file.storage_key = storage_key

    c.status = "uploading"
    db.commit()
    return UploadUrlResponse(
        upload_url=upload_url,
        storage_key=storage_key,
        consultation_id=consultation_id,
    )


@router.post("/{consultation_id}/process")
def process_consultation(
    consultation_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = _get_owned(consultation_id, doctor, db)
    audio_file = db.query(AudioFile).filter(AudioFile.consultation_id == consultation_id).first()
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file registered")

    audio_file.upload_completed_at = datetime.utcnow()
    c.status = "uploaded"
    db.commit()

    background_tasks.add_task(process_consultation_pipeline, consultation_id, db)
    return {"message": "Processing started", "consultation_id": str(consultation_id)}


@router.get("/{consultation_id}/status", response_model=ConsultationStatusResponse)
def get_status(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = _get_owned(consultation_id, doctor, db)
    return ConsultationStatusResponse(id=c.id, status=c.status, error_message=c.error_message)


@router.put("/{consultation_id}/approve", response_model=ApprovedNoteOut)
def approve_note(
    consultation_id: uuid.UUID,
    body: ApproveNoteRequest,
    user: User = Depends(get_current_user),
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = _get_owned(consultation_id, doctor, db)
    if c.status not in ("generated", "approved"):
        raise HTTPException(status_code=400, detail="Note not ready for approval")

    generated_note = db.query(GeneratedNote).filter(
        GeneratedNote.id == body.generated_note_id,
        GeneratedNote.consultation_id == consultation_id,
    ).first()
    if not generated_note:
        raise HTTPException(status_code=404, detail="Generated note not found")

    # Replace any previous approval
    existing = db.query(ApprovedNote).filter(ApprovedNote.consultation_id == consultation_id).first()
    if existing:
        db.delete(existing)
        db.flush()

    fields_edited = [
        field for field in ("subjective", "objective", "assessment", "plan")
        if getattr(body, field) != getattr(generated_note, field)
    ]

    approved = ApprovedNote(
        consultation_id=consultation_id,
        generated_note_id=body.generated_note_id,
        subjective=body.subjective,
        objective=body.objective,
        assessment=body.assessment,
        plan=body.plan,
        was_edited=len(fields_edited) > 0,
        edit_time_seconds=body.edit_time_seconds,
        fields_edited=fields_edited,
        approved_by=user.id,
    )
    db.add(approved)
    c.status = "approved"
    db.commit()
    db.refresh(approved)
    return approved


@router.get("/{consultation_id}/pdf")
def get_pdf(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = _get_owned(consultation_id, doctor, db)
    approved = db.query(ApprovedNote).filter(ApprovedNote.consultation_id == consultation_id).first()
    if not approved:
        raise HTTPException(status_code=404, detail="No approved note found")

    doctor_user = db.query(User).filter(User.id == doctor.user_id).first()
    doctor_name = doctor_user.full_name if doctor_user else "Doctor"

    pdf_bytes = generate_pdf(
        doctor_name=doctor_name,
        clinic_name=doctor.clinic_name or "Clinic",
        patient_name=c.patient_name,
        patient_age=c.patient_age,
        patient_sex=c.patient_sex,
        consultation_date=str(c.consultation_date),
        subjective=approved.subjective or "",
        objective=approved.objective or "",
        assessment=approved.assessment or "",
        plan=approved.plan or "",
    )

    # Persist PDF to storage in background (non-blocking)
    try:
        storage_key = f"pdfs/{doctor.id}/{consultation_id}/note.pdf"
        upload_bytes(storage_key, pdf_bytes, "application/pdf")
        approved.pdf_storage_key = storage_key
        approved.pdf_generated_at = datetime.utcnow()
        db.commit()
    except Exception:
        pass  # PDF is still returned even if storage fails

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=clinical_note_{consultation_id}.pdf"
        },
    )


@router.post("/{consultation_id}/regenerate")
def regenerate_note(
    consultation_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = _get_owned(consultation_id, doctor, db)
    if not db.query(AudioFile).filter(AudioFile.consultation_id == consultation_id).first():
        raise HTTPException(status_code=400, detail="No audio file for this consultation")
    # Reset to transcribed so pipeline re-runs generation only
    c.status = "transcribed"
    c.error_message = None
    db.commit()
    background_tasks.add_task(process_consultation_pipeline, consultation_id, db)
    return {"message": "Regeneration started", "consultation_id": str(consultation_id)}


@router.get("", response_model=list[ConsultationListItem])
def list_consultations(
    skip: int = 0,
    limit: int = 20,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    return (
        db.query(Consultation)
        .filter(Consultation.doctor_id == doctor.id, Consultation.is_deleted == False)
        .order_by(Consultation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{consultation_id}", response_model=ConsultationOut)
def get_consultation(
    consultation_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    c = (
        db.query(Consultation)
        .options(
            joinedload(Consultation.transcript),
            joinedload(Consultation.generated_notes),
            joinedload(Consultation.approved_note),
        )
        .filter(
            Consultation.id == consultation_id,
            Consultation.doctor_id == doctor.id,
            Consultation.is_deleted == False,
        )
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return _to_out(c)
