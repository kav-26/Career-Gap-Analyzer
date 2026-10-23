from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.document import Document
from app.models.job_requirement import JobRequirementRow
from app.services.llm.factory import get_llm
from app.services.job_extraction import extract_requirements

router = APIRouter(prefix="/documents", tags=["jobs"])


@router.post("/{doc_id}/extract-requirements")
def run_requirement_extraction(doc_id: int, force: bool = False, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.kind != "job":
        raise HTTPException(400, "This document is not a job posting (kind must be 'job')")

    # Reuse earlier results unless ?force=true is passed
    if not force:
        cached = db.query(JobRequirementRow).filter_by(document_id=doc_id).all()
        if cached:
            return {
                "document_id": doc_id,
                "count": len(cached),
                "cached": True,
                "requirements": [
                    {"name": r.name, "importance": r.importance, "evidence": r.evidence} for r in cached
                ],
            }

    try:
        reqs = extract_requirements(doc.text, get_llm())
    except Exception as e:
        raise HTTPException(502, f"Requirement extraction failed: {e}")

    db.query(JobRequirementRow).filter_by(document_id=doc_id).delete()  # re-run safe
    for r in reqs:
        db.add(JobRequirementRow(
            document_id=doc_id, name=r.name, importance=r.importance, evidence=r.evidence
        ))
    db.commit()
    return {
        "document_id": doc_id,
        "count": len(reqs),
        "requirements": [r.model_dump() for r in reqs],
    }


@router.get("/{doc_id}/requirements")
def get_requirements(doc_id: int, db: Session = Depends(get_db)):
    rows = db.query(JobRequirementRow).filter_by(document_id=doc_id).all()
    return [{"name": r.name, "importance": r.importance, "evidence": r.evidence} for r in rows]
