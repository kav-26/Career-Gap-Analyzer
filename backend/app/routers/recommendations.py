import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.analysis import Analysis
from app.models.recommendation import Recommendation
from app.services.llm.factory import get_llm
from app.services.recommendations import recommend_projects

router = APIRouter(prefix="/analysis", tags=["recommendations"])


@router.post("/{analysis_id}/recommendations")
def create_recommendations(analysis_id: int, force: bool = False, db: Session = Depends(get_db)):
    row = db.get(Analysis, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")

    # Reuse saved recommendations unless ?force=true is passed
    if not force:
        saved = db.query(Recommendation).filter_by(analysis_id=analysis_id).first()
        if saved:
            return {"analysis_id": analysis_id, "cached": True, **json.loads(saved.result_json)}

    try:
        result = recommend_projects(json.loads(row.result_json), get_llm())
    except Exception as e:
        raise HTTPException(502, f"Recommendation failed: {e}")

    db.query(Recommendation).filter_by(analysis_id=analysis_id).delete()  # re-run safe
    db.add(Recommendation(analysis_id=analysis_id, result_json=json.dumps(result)))
    db.commit()
    return {"analysis_id": analysis_id, **result}


@router.get("/{analysis_id}/recommendations")
def get_recommendations(analysis_id: int, db: Session = Depends(get_db)):
    row = db.query(Recommendation).filter_by(analysis_id=analysis_id).first()
    if not row:
        raise HTTPException(404, "No recommendations yet. Run POST first.")
    return {"analysis_id": analysis_id, **json.loads(row.result_json)}
