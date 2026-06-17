import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"))
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_age: Mapped[int | None] = mapped_column(Integer)
    patient_sex: Mapped[str | None] = mapped_column(String(10))
    consultation_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(30), default="created", index=True)
    # Status flow: created → uploading → uploaded → transcribing → transcribed → generating → generated → approved → failed
    error_message: Mapped[str | None] = mapped_column(Text)
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="consultations")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="consultations")
    audio_file: Mapped["AudioFile"] = relationship("AudioFile", back_populates="consultation", uselist=False)
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="consultation", uselist=False)
    generated_notes: Mapped[list["GeneratedNote"]] = relationship(
        "GeneratedNote", back_populates="consultation", order_by="GeneratedNote.created_at.desc()"
    )
    approved_note: Mapped["ApprovedNote"] = relationship("ApprovedNote", back_populates="consultation", uselist=False)
