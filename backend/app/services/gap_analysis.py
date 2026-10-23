from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.extracted_skill import ExtractedSkillRow
from app.models.job_requirement import JobRequirementRow
from app.services.llm.base import LLMClient
from app.services.matching import match_requirements

LEVEL_RANK = {"exposure": 1, "working": 2, "proficient": 3}
LEVEL_SCORE = {"exposure": 0.4, "working": 0.75, "proficient": 1.0}
RELATION_FACTOR = {"same": 1.0, "related": 0.5, "none": 0.0}
IMPORTANCE_WEIGHT = {"must_have": 2, "nice_to_have": 1}


def status_for(score: float) -> str:
    if score >= 0.7:
        return "covered"
    if score >= 0.2:
        return "partial"
    return "missing"


def merge_skills(rows, doc_names: dict) -> dict:
    """Combine skills from several syllabi. If a skill appears more than once, keep the highest level."""
    merged: dict = {}
    for r in rows:
        key = r.name.strip().lower()
        cur = merged.get(key)
        if cur is None or LEVEL_RANK[r.level] > LEVEL_RANK[cur["level"]]:
            merged[key] = {
                "name": r.name,
                "level": r.level,
                "evidence": r.evidence,
                "source": doc_names.get(r.document_id, "unknown"),
            }
    return merged


def run_analysis(db: Session, job_id: int, syllabus_ids: list[int], llm: LLMClient) -> dict:
    skill_rows = (
        db.query(ExtractedSkillRow)
        .filter(ExtractedSkillRow.document_id.in_(syllabus_ids))
        .all()
    )
    req_rows = db.query(JobRequirementRow).filter_by(document_id=job_id).all()

    if not skill_rows:
        raise ValueError("No extracted skills found for these syllabi. Run extract-skills on each one first.")
    if not req_rows:
        raise ValueError("No requirements found for this job. Run extract-requirements first.")

    docs = db.query(Document).filter(Document.id.in_(syllabus_ids)).all()
    doc_names = {d.id: d.filename for d in docs}
    skills = merge_skills(skill_rows, doc_names)

    matches = match_requirements(
        [r.name for r in req_rows],
        [s["name"] for s in skills.values()],
        llm,
    )

    items = []
    for req, m in zip(req_rows, matches):
        skill = skills.get(m.matched_skill.strip().lower()) if m.matched_skill else None
        if skill is None:
            relation, score = "none", 0.0
        else:
            relation = m.relation
            score = LEVEL_SCORE[skill["level"]] * RELATION_FACTOR[relation]

        items.append({
            "requirement": req.name,
            "importance": req.importance,
            "category": m.category,
            "status": status_for(score),
            "score": round(score, 2),
            "relation": relation,
            "matched_skill": skill["name"] if skill else None,
            "student_level": skill["level"] if skill else None,
            "student_evidence": skill["evidence"] if skill else None,
            "source_document": skill["source"] if skill else None,
            "job_evidence": req.evidence,
            "reason": m.reason,
        })

    # Overall weighted score (must-have counts double)
    total_w = sum(IMPORTANCE_WEIGHT[i["importance"]] for i in items)
    got = sum(IMPORTANCE_WEIGHT[i["importance"]] * i["score"] for i in items)
    match_score = round(100 * got / total_w, 1) if total_w else 0.0

    must = [i for i in items if i["importance"] == "must_have"]
    must_have_covered = (
        round(100 * sum(1 for i in must if i["status"] == "covered") / len(must), 1)
        if must else None
    )

    counts = {"covered": 0, "partial": 0, "missing": 0}
    for i in items:
        counts[i["status"]] += 1

    # Data for the radar chart: weighted coverage per category
    cats: dict = {}
    for i in items:
        w = IMPORTANCE_WEIGHT[i["importance"]]
        c = cats.setdefault(i["category"], {"w": 0, "got": 0, "n": 0})
        c["w"] += w
        c["got"] += w * i["score"]
        c["n"] += 1
    radar = [
        {"category": name, "coverage": round(100 * c["got"] / c["w"], 1), "requirements": c["n"]}
        for name, c in cats.items()
    ]

    return {
        "match_score": match_score,
        "must_have_covered_pct": must_have_covered,
        "counts": counts,
        "radar": radar,
        "requirements": items,
    }
