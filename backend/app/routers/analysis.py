import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.analysis import Analysis
from app.models.document import Document
from app.services.gap_analysis import run_analysis
from app.services.llm.factory import get_llm

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    job_document_id: int
    syllabus_document_ids: list[int]


@router.post("")
def create_analysis(body: AnalysisRequest, force: bool = False, db: Session = Depends(get_db)):
    job = db.get(Document, body.job_document_id)
    if not job or job.kind != "job":
        raise HTTPException(400, "job_document_id must be an uploaded document with kind 'job'")
    if not body.syllabus_document_ids:
        raise HTTPException(400, "Provide at least one syllabus document id")
    for sid in body.syllabus_document_ids:
        d = db.get(Document, sid)
        if not d or d.kind not in {"syllabus", "transcript"}:
            raise HTTPException(400, f"Document {sid} must be a syllabus or transcript")

    # Same job + same syllabi analysed before? Reuse it unless ?force=true is passed
    wanted = sorted(set(body.syllabus_document_ids))
    if not force:
        previous = (
            db.query(Analysis)
            .filter_by(job_document_id=body.job_document_id)
            .order_by(Analysis.id.desc())
            .all()
        )
        for row in previous:
            ids = sorted({int(x) for x in row.syllabus_ids.split(",") if x})
            if ids == wanted:
                return {"analysis_id": row.id, "cached": True, **json.loads(row.result_json)}

    try:
        result = run_analysis(db, body.job_document_id, body.syllabus_document_ids, get_llm())
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Analysis failed: {e}")

    row = Analysis(
        job_document_id=body.job_document_id,
        syllabus_ids=",".join(str(i) for i in body.syllabus_document_ids),
        match_score=result["match_score"],
        result_json=json.dumps(result),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"analysis_id": row.id, **result}


@router.get("/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    row = db.get(Analysis, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    return {"analysis_id": row.id, **json.loads(row.result_json)}


@router.get("")
def list_analyses(db: Session = Depends(get_db)):
    rows = db.query(Analysis).order_by(Analysis.id.desc()).all()
    return [
        {"analysis_id": r.id, "job_document_id": r.job_document_id,
         "match_score": r.match_score, "created_at": r.created_at.isoformat()}
        for r in rows
    ]
