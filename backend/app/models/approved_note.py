import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class ApprovedNote(Base):
    __tablename__ = "approved_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False)
    generated_note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("generated_notes.id"), nullable=False)

    subjective: Mapped[str | None] = mapped_column(Text)
    objective: Mapped[str | None] = mapped_column(Text)
    assessment: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str | None] = mapped_column(Text)

    was_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edit_time_seconds: Mapped[int | None] = mapped_column(Integer)
    fields_edited: Mapped[list] = mapped_column(JSONB, default=list)

    approved_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    pdf_storage_key: Mapped[str | None] = mapped_column(String(500))
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="approved_note")
    generated_note: Mapped["GeneratedNote"] = relationship("GeneratedNote")
    approver: Mapped["User"] = relationship("User")
