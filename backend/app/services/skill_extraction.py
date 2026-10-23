from typing import Literal
from pydantic import BaseModel, ValidationError
from app.services.llm.base import LLMClient

MAX_CHARS = 12000  # keeps cost and latency down


class ExtractedSkill(BaseModel):
    name: str
    level: Literal["exposure", "working", "proficient"]
    evidence: str


class SkillExtraction(BaseModel):
    skills: list[ExtractedSkill]


SYSTEM = """You extract skills from university course documents (syllabi).

Rules:
- Only include skills clearly supported by the text. Never guess or add skills the document does not mention.
- Use short, standard skill names, such as "SQL", "Machine Learning", "REST APIs", "Data Structures".
- level: "exposure" = only mentioned or introduced; "working" = assignments, labs or exercises use it; "proficient" = a major project or heavy emphasis.
- evidence: a short phrase (under 20 words) copied from the document that supports the skill.
- Skip generic fluff like "teamwork" unless it is clearly assessed. Return at most 30 skills.
"""


def extract_skills(text: str, llm: LLMClient) -> list[ExtractedSkill]:
    user = f"Document:\n{text[:MAX_CHARS]}"
    last_error: Exception | None = None
    for _ in range(2):  # one retry if the model returns bad JSON
        try:
            raw = llm.complete_json(SYSTEM, user, SkillExtraction.model_json_schema())
            return SkillExtraction.model_validate(raw).skills
        except (ValueError, ValidationError) as e:
            last_error = e
    raise last_error
