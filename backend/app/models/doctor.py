import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(100))
    specialization: Mapped[str] = mapped_column(String(100), default="Orthopedics")
    clinic_name: Mapped[str | None] = mapped_column(String(255))
    clinic_address: Mapped[str | None] = mapped_column(Text)
    preferred_language: Mapped[str] = mapped_column(String(20), default="hinglish")
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_ends: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consultations_this_month: Mapped[int] = mapped_column(Integer, default=0)
    free_quota: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="doctor")
    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="doctor")
    consultations: Mapped[list["Consultation"]] = relationship("Consultation", back_populates="doctor")
