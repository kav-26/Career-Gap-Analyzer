import json
from typing import Literal
from pydantic import BaseModel, ValidationError
from app.services.llm.base import LLMClient

Category = Literal[
    "Programming", "Databases", "Web & APIs", "Cloud & DevOps",
    "Data & ML", "Tools & Practices", "Soft Skills", "Other",
]


class MatchItem(BaseModel):
    requirement: str
    category: Category
    matched_skill: str | None = None
    relation: Literal["same", "related", "none"]
    reason: str


class MatchResult(BaseModel):
    matches: list[MatchItem]


SYSTEM = """You compare a job's required skills with a student's skills.

For EACH requirement, in the same order given, return one entry:
- requirement: copy the requirement text exactly.
- category: choose the best fit from the allowed categories.
- matched_skill: the single best matching skill from the student's skill list, copied EXACTLY as written there. Use null if nothing is relevant.
- relation:
  "same"    = the student's skill clearly covers the requirement (for example SQL for SQL, Python for Python, MySQL for "relational databases").
  "related" = an adjacent or transferable skill (for example Flask for FastAPI, or MongoDB for a broader requirement).
  "none"    = nothing in the list is relevant.
- reason: one short sentence explaining the decision.

Special cases:
- ALTERNATIVES: if the requirement offers a choice (for example "AWS or GCP", "FastAPI or Flask", "PostgreSQL or MySQL"),
  the student only needs ANY ONE of them. Use "same" if the student has any one of the options; use "related" only if the student has a closely related skill but none of the options.
- CATEGORY WITH EXAMPLES: if the requirement is an area with examples in brackets (for example "NoSQL databases (e.g. MongoDB)"),
  use "same" if the student has the area itself or any listed example.
- COMBINED REQUIREMENTS: for something like "SQL and relational databases (PostgreSQL or MySQL)", match the student's closest skill (for example SQL or MySQL).

Rules:
- Only use skills from the student's list. Never invent skills.
- Be strict: do not mark "same" unless the skill truly covers the requirement.
"""


def match_requirements(requirements: list[str], skills: list[str], llm: LLMClient) -> list[MatchItem]:
    user = json.dumps({"requirements": requirements, "student_skills": skills})

    result = None
    last_error: Exception | None = None
    for _ in range(2):  # one retry if the model returns bad JSON
        try:
            raw = llm.complete_json(SYSTEM, user, MatchResult.model_json_schema())
            result = MatchResult.model_validate(raw)
            break
        except (ValueError, ValidationError) as e:
            last_error = e
    if result is None:
        raise last_error

    skill_lookup = {s.lower(): s for s in skills}
    by_req = {m.requirement.strip().lower(): m for m in result.matches}

    out: list[MatchItem] = []
    for req in requirements:
        m = by_req.get(req.strip().lower())
        if m is None:  # the model skipped it
            m = MatchItem(requirement=req, category="Other", matched_skill=None,
                          relation="none", reason="No match returned by the model")
        elif (m.matched_skill is None
              or m.relation == "none"
              or m.matched_skill.strip().lower() not in skill_lookup):  # guard against invented skills
            m = m.model_copy(update={"matched_skill": None, "relation": "none"})
        out.append(m)
    return out
