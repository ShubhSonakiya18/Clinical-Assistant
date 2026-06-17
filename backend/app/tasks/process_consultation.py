import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.consultation import Consultation
from app.models.audio_file import AudioFile
from app.models.transcript import Transcript
from app.models.generated_note import GeneratedNote
from app.models.prompt_version import PromptVersion
from app.services.audio_service import get_audio_bytes
from app.services.transcription_service import transcribe
from app.services.note_service import generate_soap_note


def get_or_create_active_prompt(db: Session) -> PromptVersion:
    pv = db.query(PromptVersion).filter(PromptVersion.is_active == True).first()
    if not pv:
        pv = PromptVersion(
            version_tag="v1.0",
            template="default",
            description="Initial SOAP generation prompt",
            is_active=True,
        )
        db.add(pv)
        db.commit()
        db.refresh(pv)
    return pv


def process_consultation_pipeline(consultation_id: uuid.UUID, db: Session) -> None:
    """
    BackgroundTask handler: transcribe audio → generate SOAP note.
    Updates consultation.status at each step so the frontend can poll progress.
    """
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        return

    try:
        # ── Step 1: Transcribe ───────────────────────────────────────────────
        consultation.status = "transcribing"
        db.commit()

        audio_file = db.query(AudioFile).filter(AudioFile.consultation_id == consultation_id).first()
        if not audio_file:
            raise ValueError("No audio file found for this consultation")

        audio_bytes = get_audio_bytes(audio_file.storage_key)
        result = transcribe(audio_bytes)

        # Remove existing transcript if regenerating
        existing_transcript = db.query(Transcript).filter(Transcript.consultation_id == consultation_id).first()
        if existing_transcript:
            db.delete(existing_transcript)
            db.flush()

        transcript = Transcript(
            consultation_id=consultation_id,
            raw_text=result["text"],
            detected_language=result.get("language"),
            transcription_provider=result.get("provider"),
            transcription_model=result.get("model"),
            processing_time_ms=result.get("processing_time_ms"),
            word_count=len(result["text"].split()),
        )
        db.add(transcript)
        consultation.status = "transcribed"
        db.commit()

        # ── Step 2: Generate SOAP note ───────────────────────────────────────
        consultation.status = "generating"
        db.commit()

        patient_context = f"Name: {consultation.patient_name}"
        if consultation.patient_age:
            patient_context += f", Age: {consultation.patient_age} years"
        if consultation.patient_sex:
            patient_context += f", Sex: {consultation.patient_sex}"

        note_result = generate_soap_note(result["text"], patient_context)
        prompt_version = get_or_create_active_prompt(db)

        generated_note = GeneratedNote(
            consultation_id=consultation_id,
            prompt_version_id=prompt_version.id,
            subjective=note_result["subjective"],
            objective=note_result["objective"],
            assessment=note_result["assessment"],
            plan=note_result["plan"],
            missing_information=note_result["missing_information"],
            ai_model=note_result["ai_model"],
            generation_time_ms=note_result.get("generation_time_ms"),
            input_tokens=note_result.get("input_tokens"),
            output_tokens=note_result.get("output_tokens"),
            raw_response=note_result.get("raw_response"),
        )
        db.add(generated_note)

        # Extract chief complaint from first line of subjective
        subjective = note_result.get("subjective", "")
        if subjective and subjective.strip() != "Not documented.":
            first_line = subjective.strip().split("\n")[0]
            consultation.chief_complaint = first_line[:200]

        consultation.status = "generated"
        db.commit()

    except Exception as e:
        consultation.status = "failed"
        consultation.error_message = str(e)[:500]
        db.commit()
        raise
