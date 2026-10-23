from typing import Literal
from pydantic import BaseModel, ValidationError
from app.services.llm.base import LLMClient
from app.services.normalize import canonical_name

MAX_CHARS = 12000  # keeps cost and latency down
LEVEL_RANK = {"exposure": 1, "working": 2, "proficient": 3}


class ExtractedSkill(BaseModel):
    name: str
    level: Literal["exposure", "working", "proficient"]
    evidence: str


class SkillExtraction(BaseModel):
    skills: list[ExtractedSkill]


SYSTEM = """You extract skills from university course documents (syllabi).

Rules:
- Be thorough and fine-grained. List every distinct tool, library, language, technique and concept that the units,
  labs and project name, including topics that are only introduced. Split broad areas into the specific topics the
  document names. For example, list "Flexbox", "CSS Grid" and "Responsive Design" separately from "CSS", and list
  "k-Nearest Neighbors", "Random Forests" and "Model Evaluation" separately from "Machine Learning".
- Only include skills clearly supported by the text. Never add skills the document does not mention.
- Use short, standard skill names, such as "SQL", "Machine Learning", "REST APIs", "Data Structures".
- One entry per skill. Never list the same skill twice under different names.
- level:
  "exposure"   = only mentioned or introduced, or described as "introduction", "introductory", "basics of" or
                 "a first look" (even if one lab uses it);
  "working"    = practised repeatedly in assignments or labs;
  "proficient" = a major project or heavy emphasis across the course.
- evidence: a short phrase (under 20 words) copied from the document that supports the skill.
- Skip generic fluff like "teamwork" unless it is clearly assessed. Return at most 40 skills.
"""


def clean(skills: list[ExtractedSkill]) -> list[ExtractedSkill]:
    """Give each skill its standard name and keep one entry per skill (the highest level)."""
    best: dict[str, ExtractedSkill] = {}
    for s in skills:
        name = canonical_name(s.name)
        key = name.lower()
        s = s.model_copy(update={"name": name})
        current = best.get(key)
        if current is None or LEVEL_RANK[s.level] > LEVEL_RANK[current.level]:
            best[key] = s
    return list(best.values())


def extract_skills(text: str, llm: LLMClient) -> list[ExtractedSkill]:
    user = f"Document:\n{text[:MAX_CHARS]}"
    last_error: Exception | None = None
    for _ in range(2):  # one retry if the model returns bad JSON
        try:
            raw = llm.complete_json(SYSTEM, user, SkillExtraction.model_json_schema())
            return clean(SkillExtraction.model_validate(raw).skills)
        except (ValueError, ValidationError) as e:
            last_error = e
    raise last_error
