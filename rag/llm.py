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
            # Current Claude models think before answering, and that thinking
            # counts toward max_tokens. A tight cap can use up the whole budget
            # on thinking and return a cut-off or empty answer.
            max_tokens=config.MAX_TOKENS,
            output_config={"effort": config.LLM_EFFORT},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Anything other than a normal finish (cut off by max_tokens, declined
        # by a safety check) returns "", which the pipeline turns into the
        # fixed fallback. Never show a customer half a sentence.
        if response.stop_reason != "end_turn":
            print(f"[llm] stop_reason={response.stop_reason}; using fallback")
            return ""
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
