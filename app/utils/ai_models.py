"""AI model configuration supporting both OpenAI and Ollama providers."""

import os
import httpx
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from openai import OpenAI
from utils.common import logger


@dataclass
class AIProvider:
    """Unified AI provider interface supporting OpenAI and Ollama."""
    provider: str = "openai"  # "openai" or "ollama"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    def __post_init__(self):
        if self.provider == "openai":
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == "ollama":
            # Ollama uses OpenAI-compatible API
            self._client = OpenAI(
                base_url=self.base_url or "http://localhost:11434/v1",
                api_key=self.api_key or "ollama"  # Ollama doesn't require real API key
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def invoke(self, prompt: str, system_prompt: str = "You are AlitaOS, a helpful assistant."):
        """Minimal interface compatible with app code."""
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=800,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM invoke error: {e}")
            raise

    def stream(self, prompt: str, system_prompt: str = "You are AlitaOS, a helpful assistant."):
        """Stream response for real-time applications."""
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=800,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            raise


def get_ollama_models() -> List[str]:
    """Get available Ollama models from local installation."""
    try:
        with httpx.Client() as client:
            response = client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                logger.warning(f"Failed to fetch Ollama models: {response.status_code}")
                return []
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        return []

def is_ollama_available() -> bool:
    """Check if Ollama is running locally."""
    try:
        with httpx.Client() as client:
            response = client.get("http://localhost:11434/api/version", timeout=3.0)
            return response.status_code == 200
    except Exception:
        return False

def get_llm(task: str = "default", provider: str = None, model: str = None) -> AIProvider:
    """Return a configured AI provider client for the specified task."""
    import streamlit as st
    
    # Get provider and model from session state or use defaults
    if provider is None:
        provider = st.session_state.get("ai_provider", "openai")
    if model is None:
        model = st.session_state.get("ai_model", "gpt-4o-mini")
    
    # Task-specific temperature adjustments
    temperature = 0.2
    if task == "image_prompt":
        temperature = 0.7
    elif task == "creative_content":
        temperature = 0.5
    elif task in ["python_code", "sql_generation"]:
        temperature = 0.1
    
    return AIProvider(
        provider=provider,
        model=model,
        temperature=temperature,
        api_key=os.environ.get("OPENAI_API_KEY") if provider == "openai" else None
    )

# Backward compatibility
SimpleOpenAI = AIProvider
