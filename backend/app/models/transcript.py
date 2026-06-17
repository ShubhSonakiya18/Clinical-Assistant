import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(20))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    transcription_provider: Mapped[str | None] = mapped_column(String(50))
    transcription_model: Mapped[str | None] = mapped_column(String(100))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    word_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="transcript")
