from app.services.llm.base import LLMClient, build_system, parse_json


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or "claude-haiku-5-5"

    def complete_json(self, system: str, user: str, schema: dict) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=build_system(system, schema),
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return parse_json(text)
