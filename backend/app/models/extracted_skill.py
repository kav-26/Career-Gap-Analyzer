from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class ExtractedSkillRow(Base):
    __tablename__ = "extracted_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    name: Mapped[str] = mapped_column(String(120))
    level: Mapped[str] = mapped_column(String(20))
    evidence: Mapped[str] = mapped_column(Text)
