from typing import Literal
from pydantic import BaseModel, ValidationError
from app.services.llm.base import LLMClient
from app.services.normalize import canonical_name

MAX_CHARS = 12000
IMPORTANCE_RANK = {"must_have": 2, "nice_to_have": 1}


class Requirement(BaseModel):
    name: str
    importance: Literal["must_have", "nice_to_have"]
    evidence: str


class JobExtraction(BaseModel):
    requirements: list[Requirement]


SYSTEM = """You extract required skills from job postings.

Rules:
- Only include skills, tools, or knowledge areas clearly stated in the posting. Never invent requirements.
- Use short, standard skill names, such as "Python", "SQL", "REST APIs", "Docker", "AWS", "Git".
- ONE requirement per concept. Never list the same idea twice.
- ALTERNATIVES: when the posting offers a choice ("X or Y", "PostgreSQL or MySQL", "FastAPI or Flask", "AWS or GCP"),
  output ONE requirement named "X or Y" (for example "AWS or GCP", "FastAPI or Flask"). Do NOT output X and Y as separate entries.
- CATEGORY WITH EXAMPLES: when a general area is given with example tools ("NoSQL databases such as MongoDB"),
  output ONE requirement using the area name and put the examples in brackets: "NoSQL databases (e.g. MongoDB)".
  Do not also list the example on its own.
- SAME BULLET, SAME AREA: if two phrases in one bullet describe the same skill area
  ("SQL and relational databases such as PostgreSQL or MySQL"), merge them into one requirement,
  for example "SQL and relational databases (PostgreSQL or MySQL)".
- importance: "must_have" for requirements, "required", "strong knowledge", or "experience with".
  "nice_to_have" for "nice to have", "preferred", "bonus", "plus", "familiarity", or "exposure".
  If unclear, use "must_have" for the main requirements list and "nice_to_have" for optional lists.
- Skip company descriptions, benefits, and vague phrases like "team player" or "passionate".
- evidence: a short phrase (under 20 words) copied from the posting that supports the requirement.
- Requirement names must be under 70 characters. Return at most 30 requirements.
"""


def clean(reqs: list[Requirement]) -> list[Requirement]:
    """Standard names, and one entry per requirement (must-have wins over nice-to-have)."""
    best: dict[str, Requirement] = {}
    for r in reqs:
        name = canonical_name(r.name)
        key = name.lower()
        r = r.model_copy(update={"name": name})
        current = best.get(key)
        if current is None or IMPORTANCE_RANK[r.importance] > IMPORTANCE_RANK[current.importance]:
            best[key] = r
    return list(best.values())


def extract_requirements(text: str, llm: LLMClient) -> list[Requirement]:
    user = f"Job posting:\n{text[:MAX_CHARS]}"
    last_error: Exception | None = None
    for _ in range(2):  # one retry if the model returns bad JSON
        try:
            raw = llm.complete_json(SYSTEM, user, JobExtraction.model_json_schema())
            return clean(JobExtraction.model_validate(raw).requirements)
        except (ValueError, ValidationError) as e:
            last_error = e
    raise last_error
