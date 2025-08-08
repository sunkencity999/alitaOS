"""AI model configuration using the official OpenAI SDK (no LangChain)."""

import os
from dataclasses import dataclass
from openai import OpenAI
from utils.common import logger


@dataclass
class SimpleOpenAI:
    model: str = "gpt-4o-mini"
    temperature: float = 0.2

    def __post_init__(self):
        self._client = OpenAI()

    def invoke(self, prompt: str):
        """Minimal interface compatible with app code."""
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are AlitaOS, a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=800,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM invoke error: {e}")
            raise


def get_llm(task: str = "default") -> SimpleOpenAI:
    """Return a configured SimpleOpenAI client for the specified task."""
    # Basic routing; can be extended as needed
    if task == "image_prompt":
        return SimpleOpenAI(model="gpt-4o-mini", temperature=0.7)
    return SimpleOpenAI(model="gpt-4o-mini", temperature=0.2)
