from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.document import Document
from app.models.extracted_skill import ExtractedSkillRow
from app.services.llm.factory import get_llm
from app.services.skill_extraction import extract_skills

router = APIRouter(prefix="/documents", tags=["skills"])


@router.post("/{doc_id}/extract-skills")
def run_extraction(doc_id: int, force: bool = False, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    # Reuse earlier results unless ?force=true is passed
    if not force:
        cached = db.query(ExtractedSkillRow).filter_by(document_id=doc_id).all()
        if cached:
            return {
                "document_id": doc_id,
                "count": len(cached),
                "cached": True,
                "skills": [{"name": r.name, "level": r.level, "evidence": r.evidence} for r in cached],
            }

    try:
        skills = extract_skills(doc.text, get_llm())
    except Exception as e:
        raise HTTPException(502, f"Skill extraction failed: {e}")

    db.query(ExtractedSkillRow).filter_by(document_id=doc_id).delete()  # re-run safe
    for s in skills:
        db.add(ExtractedSkillRow(document_id=doc_id, name=s.name, level=s.level, evidence=s.evidence))
    db.commit()
    return {"document_id": doc_id, "count": len(skills), "skills": [s.model_dump() for s in skills]}


@router.get("/{doc_id}/skills")
def get_skills(doc_id: int, db: Session = Depends(get_db)):
    rows = db.query(ExtractedSkillRow).filter_by(document_id=doc_id).all()
    return [{"name": r.name, "level": r.level, "evidence": r.evidence} for r in rows]
