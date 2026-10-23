from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class JobRequirementRow(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    name: Mapped[str] = mapped_column(String(120))
    importance: Mapped[str] = mapped_column(String(20))  # must_have | nice_to_have
    evidence: Mapped[str] = mapped_column(Text)
