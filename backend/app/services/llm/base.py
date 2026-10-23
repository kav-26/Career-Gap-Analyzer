import json
import re
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete_json(self, system: str, user: str, schema: dict) -> dict:
        """Send a prompt and return parsed JSON matching the schema."""


def build_system(system: str, schema: dict) -> str:
    return (
        f"{system}\n\nReturn ONLY valid JSON matching this JSON schema. "
        f"No explanations, no markdown fences.\n{json.dumps(schema)}"
    )


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON")
    return json.loads(text[start : end + 1])
