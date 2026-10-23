import json
from typing import Literal
from pydantic import BaseModel, ValidationError
from app.services.llm.base import LLMClient

IMPORTANCE_WEIGHT = {"must_have": 2, "nice_to_have": 1}
MAX_GAPS = 12
MAX_PROJECTS = 5


class Project(BaseModel):
    title: str
    description: str
    gaps_addressed: list[str]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    estimated_weeks: int
    deliverables: list[str]
    resume_bullet: str


class ProjectSet(BaseModel):
    projects: list[Project]


SYSTEM = """You are a career mentor for university students.

You receive: (1) the student's existing strengths and (2) a list of skill gaps for a target job.
Propose 3 to 5 portfolio projects that together close the most important gaps.

Rules:
- Each project should address SEVERAL related gaps at once. Combine them sensibly.
- gaps_addressed: copy gap names EXACTLY as given in the gap list. Never invent gap names.
- Build on the student's existing strengths so the project is realistic for them.
- Each project must be buildable by one student, using free tools only.
- description: 2 to 3 sentences on what to build and why it proves the skills.
- deliverables: 3 to 5 concrete items (for example "Dockerized API", "README with architecture diagram").
- estimated_weeks: a whole number from 1 to 8.
- resume_bullet: one achievement-style bullet the student could put on a resume AFTER finishing. Do not invent numbers or results.
- Prioritize must-have gaps over nice-to-have gaps.
"""


def recommend_projects(analysis: dict, llm: LLMClient) -> dict:
    items = analysis["requirements"]
    gaps = [i for i in items if i["status"] != "covered"]
    if not gaps:
        return {"message": "No gaps found. This job is already well covered.", "projects": []}

    def impact_of(i: dict) -> float:
        return IMPORTANCE_WEIGHT[i["importance"]] * (1 - i["score"])

    gaps.sort(key=impact_of, reverse=True)
    gaps = gaps[:MAX_GAPS]
    gap_impact = {g["requirement"].strip().lower(): impact_of(g) for g in gaps}
    total_impact = sum(gap_impact.values()) or 1.0

    strengths = sorted({
        i["matched_skill"] for i in items
        if i["status"] == "covered" and i["matched_skill"]
    })

    user = json.dumps({
        "student_strengths": strengths,
        "gaps": [
            {"name": g["requirement"], "importance": g["importance"], "status": g["status"]}
            for g in gaps
        ],
    })

    result = None
    last_error: Exception | None = None
    for _ in range(2):  # one retry if the model returns bad JSON
        try:
            raw = llm.complete_json(SYSTEM, user, ProjectSet.model_json_schema())
            result = ProjectSet.model_validate(raw)
            break
        except (ValueError, ValidationError) as e:
            last_error = e
    if result is None:
        raise last_error

    canonical = {g["requirement"].strip().lower(): g["requirement"] for g in gaps}
    projects = []
    for p in result.projects:
        valid, seen = [], set()
        for name in p.gaps_addressed:
            key = name.strip().lower()
            if key in canonical and key not in seen:  # drop invented or duplicate gaps
                valid.append(canonical[key])
                seen.add(key)
        if not valid:
            continue
        impact = sum(gap_impact[k] for k in seen)
        projects.append({
            "title": p.title,
            "description": p.description,
            "gaps_addressed": valid,
            "difficulty": p.difficulty,
            "estimated_weeks": max(1, min(p.estimated_weeks, 12)),
            "deliverables": p.deliverables,
            "resume_bullet": p.resume_bullet,
            "impact_pct": round(100 * impact / total_impact, 1),
        })

    projects.sort(key=lambda x: x["impact_pct"], reverse=True)
    covered = {g.lower() for p in projects[:MAX_PROJECTS] for g in p["gaps_addressed"]}
    return {
        "projects": projects[:MAX_PROJECTS],
        "gaps_not_covered": [g["requirement"] for g in gaps if g["requirement"].lower() not in covered],
    }
