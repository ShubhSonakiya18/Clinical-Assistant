"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_verified", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("registration_number", sa.String(100)),
        sa.Column("specialization", sa.String(100), server_default="Orthopedics"),
        sa.Column("clinic_name", sa.String(255)),
        sa.Column("clinic_address", sa.Text),
        sa.Column("preferred_language", sa.String(20), server_default="hinglish"),
        sa.Column("subscription_tier", sa.String(20), server_default="free"),
        sa.Column("subscription_ends", sa.DateTime(timezone=True)),
        sa.Column("consultations_this_month", sa.Integer, server_default="0"),
        sa.Column("free_quota", sa.Integer, server_default="10"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("age", sa.Integer),
        sa.Column("sex", sa.String(10)),
        sa.Column("phone", sa.String(20)),
        sa.Column("notes", sa.Text),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_patients_doctor_id", "patients", ["doctor_id"])

    op.create_table(
        "consultations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="SET NULL")),
        sa.Column("patient_name", sa.String(255), nullable=False),
        sa.Column("patient_age", sa.Integer),
        sa.Column("patient_sex", sa.String(10)),
        sa.Column("consultation_date", sa.Date, server_default=sa.func.current_date()),
        sa.Column("status", sa.String(30), server_default="created"),
        sa.Column("error_message", sa.Text),
        sa.Column("chief_complaint", sa.Text),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_consultations_doctor_id", "consultations", ["doctor_id"])
    op.create_index("ix_consultations_status", "consultations", ["status"])

    op.create_table(
        "audio_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("storage_bucket", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("mime_type", sa.String(50), server_default="audio/webm"),
        sa.Column("upload_completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("detected_language", sa.String(20)),
        sa.Column("confidence_score", sa.Float),
        sa.Column("transcription_provider", sa.String(50)),
        sa.Column("transcription_model", sa.String(100)),
        sa.Column("processing_time_ms", sa.Integer),
        sa.Column("word_count", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_tag", sa.String(50), unique=True, nullable=False),
        sa.Column("template", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "generated_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=False),
        sa.Column("subjective", sa.Text),
        sa.Column("objective", sa.Text),
        sa.Column("assessment", sa.Text),
        sa.Column("plan", sa.Text),
        sa.Column("missing_information", postgresql.JSONB, server_default="[]"),
        sa.Column("ai_model", sa.String(100), nullable=False),
        sa.Column("generation_time_ms", sa.Integer),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("raw_response", postgresql.JSONB),
        sa.Column("attempt_number", sa.Integer, server_default="1"),
        sa.Column("is_valid", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_generated_notes_consultation_id", "generated_notes", ["consultation_id"])

    op.create_table(
        "approved_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consultations.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("generated_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("generated_notes.id"), nullable=False),
        sa.Column("subjective", sa.Text),
        sa.Column("objective", sa.Text),
        sa.Column("assessment", sa.Text),
        sa.Column("plan", sa.Text),
        sa.Column("was_edited", sa.Boolean, server_default="false"),
        sa.Column("edit_time_seconds", sa.Integer),
        sa.Column("fields_edited", postgresql.JSONB, server_default="[]"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("pdf_storage_key", sa.String(500)),
        sa.Column("pdf_generated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "usage_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("metric_date", sa.Date, nullable=False),
        sa.Column("consultations_created", sa.Integer, server_default="0"),
        sa.Column("notes_generated", sa.Integer, server_default="0"),
        sa.Column("notes_approved", sa.Integer, server_default="0"),
        sa.Column("avg_transcription_time_ms", sa.Float),
        sa.Column("avg_generation_time_ms", sa.Float),
        sa.Column("avg_edit_time_seconds", sa.Float),
        sa.Column("pdfs_exported", sa.Integer, server_default="0"),
        sa.Column("total_audio_seconds", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("doctor_id", "metric_date", name="uq_usage_metrics_doctor_date"),
    )
    op.create_index("ix_usage_metrics_doctor_id", "usage_metrics", ["doctor_id"])


def downgrade() -> None:
    op.drop_table("usage_metrics")
    op.drop_table("audit_logs")
    op.drop_table("approved_notes")
    op.drop_table("generated_notes")
    op.drop_table("prompt_versions")
    op.drop_table("transcripts")
    op.drop_table("audio_files")
    op.drop_table("consultations")
    op.drop_table("patients")
    op.drop_table("doctors")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
