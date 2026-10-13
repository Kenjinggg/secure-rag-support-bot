"""Provider-agnostic LLM wrapper.

Switch providers by changing LLM_PROVIDER and LLM_MODEL in .env;
nothing else in the code needs to change.
"""
from rag import config


class AnthropicLLM:
    def __init__(self, model: str):
        import anthropic  # reads ANTHROPIC_API_KEY from the environment
        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=config.MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in response.content if b.type == "text")


class OpenAILLM:
    def __init__(self, model: str):
        import openai  # pip install openai; reads OPENAI_API_KEY
        self.client = openai.OpenAI()
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


def get_llm():
    provider = config.LLM_PROVIDER.lower()
    if provider == "anthropic":
        return AnthropicLLM(config.LLM_MODEL)
    if provider == "openai":
        return OpenAILLM(config.LLM_MODEL)
    raise ValueError(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER!r}")
