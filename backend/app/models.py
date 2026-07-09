from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class CaseRecord(Base):
    __tablename__ = "case_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    report_type: Mapped[str] = mapped_column(String(16), index=True)
    display_name: Mapped[str] = mapped_column(String(140))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str] = mapped_column(String(80), index=True)
    location: Mapped[str] = mapped_column(String(180))
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="open")
    image_path: Mapped[str] = mapped_column(String(260))
    face_path: Mapped[str] = mapped_column(String(260))
    embedding: Mapped[bytes] = mapped_column(LargeBinary)
    embedding_dim: Mapped[int] = mapped_column(Integer)
    blur_variance: Mapped[float] = mapped_column(Float)
    brightness: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    reviewer_id: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(60))
    action: Mapped[str] = mapped_column(String(80))
    case_id: Mapped[str] = mapped_column(String(40), index=True)
    candidate_case_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
