from typing import Literal
from pydantic import BaseModel, ValidationError
from app.services.llm.base import LLMClient

MAX_CHARS = 12000


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
  Use ONE name per skill, so "REST API design" and "RESTful services" both become "REST APIs".
- Split combined items into separate skills ("PostgreSQL or MySQL" becomes two entries).
- importance: "must_have" for requirements, "required", "strong knowledge", or "experience with".
  "nice_to_have" for "nice to have", "preferred", "bonus", "plus", "familiarity", or "exposure".
  If unclear, use "must_have" for the main requirements list and "nice_to_have" for optional lists.
- Skip company descriptions, benefits, and vague phrases like "team player" or "passionate".
- evidence: a short phrase (under 20 words) copied from the posting that supports the skill.
- Return at most 30 requirements.
"""


def extract_requirements(text: str, llm: LLMClient) -> list[Requirement]:
    user = f"Job posting:\n{text[:MAX_CHARS]}"
    last_error: Exception | None = None
    for _ in range(2):  # one retry if the model returns bad JSON
        try:
            raw = llm.complete_json(SYSTEM, user, JobExtraction.model_json_schema())
            return JobExtraction.model_validate(raw).requirements
        except (ValueError, ValidationError) as e:
            last_error = e
    raise last_error
