from app.config import settings
from app.services.llm.base import LLMClient


def get_llm() -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        from app.services.llm.anthropic_client import AnthropicClient
        return AnthropicClient(settings.llm_api_key, settings.llm_model)
    if provider in {"openai", "openai_compatible", "ollama", "groq", "gemini"}:
        from app.services.llm.openai_client import OpenAICompatClient
        return OpenAICompatClient(
            settings.llm_api_key,
            settings.llm_model,
            settings.llm_base_url,
            settings.llm_reasoning_effort,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")
