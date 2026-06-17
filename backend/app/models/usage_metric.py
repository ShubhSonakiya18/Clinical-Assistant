import uuid
from datetime import datetime, date
from sqlalchemy import DateTime, ForeignKey, Integer, Float, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UsageMetric(Base):
    __tablename__ = "usage_metrics"
    __table_args__ = (UniqueConstraint("doctor_id", "metric_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    consultations_created: Mapped[int] = mapped_column(Integer, default=0)
    notes_generated: Mapped[int] = mapped_column(Integer, default=0)
    notes_approved: Mapped[int] = mapped_column(Integer, default=0)
    avg_transcription_time_ms: Mapped[float | None] = mapped_column(Float)
    avg_generation_time_ms: Mapped[float | None] = mapped_column(Float)
    avg_edit_time_seconds: Mapped[float | None] = mapped_column(Float)
    pdfs_exported: Mapped[int] = mapped_column(Integer, default=0)
    total_audio_seconds: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
