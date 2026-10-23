from app.services.llm.base import LLMClient, build_system, parse_json


class OpenAICompatClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str = "", reasoning_effort: str = ""):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key or "none", base_url=base_url or None)
        self.model = model
        self.reasoning_effort = reasoning_effort

    def complete_json(self, system: str, user: str, schema: dict) -> dict:
        kwargs = {}
        if self.reasoning_effort:
            # Lets Gemini skip or reduce "thinking", which makes calls much faster.
            kwargs["extra_body"] = {"reasoning_effort": self.reasoning_effort}
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": build_system(system, schema)},
                {"role": "user", "content": user},
            ],
            **kwargs,
        )
        return parse_json(resp.choices[0].message.content)
