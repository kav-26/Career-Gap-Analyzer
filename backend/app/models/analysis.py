from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_document_id: Mapped[int] = mapped_column()
    syllabus_ids: Mapped[str] = mapped_column(String(255))  # comma-separated ids
    match_score: Mapped[float] = mapped_column(Float)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
