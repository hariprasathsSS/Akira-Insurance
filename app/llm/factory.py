"""LLM provider factory — selects provider from environment.

If no LLM is configured, all methods raise LLMNotConfigured so non-LLM
APIs continue working. The application never silently falls back to a
fake response.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import LLMNotConfigured
from app.llm.interfaces import BaseLLMProvider, EmbeddingProvider


class _OpenAIProvider(BaseLLMProvider):
    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None) -> None:
        self._model = model
        self._api_key = api_key
        self._base_url = base_url

    @property
    def provider_name(self) -> str:
        return "groq" if self._base_url else "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, messages, temperature=0.0, max_tokens=1024):
        from openai import AsyncOpenAI  # type: ignore
        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        result = await client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = result.choices[0]
        return type("LLMResponse", (), {
            "content": choice.message.content,
            "model": result.model,
            "input_tokens": result.usage.prompt_tokens if result.usage else None,
            "output_tokens": result.usage.completion_tokens if result.usage else None,
        })()


class _GoogleProvider(BaseLLMProvider):
    def __init__(self, model: str, api_key: str) -> None:
        self._model = model
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(self, messages, temperature=0.0, max_tokens=1024):
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(self._model)
        prompt = "\n".join(f"{m.role}: {m.content}" for m in messages)
        response = await model.generate_content_async(prompt)
        return type("LLMResponse", (), {
            "content": response.text,
            "model": self._model,
            "input_tokens": None,
            "output_tokens": None,
        })()


class _OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str, api_key: str, dim: int) -> None:
        self._model = model
        self._api_key = api_key
        self._dim = dim

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, texts):
        from openai import AsyncOpenAI  # type: ignore
        client = AsyncOpenAI(api_key=self._api_key)
        resp = await client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in resp.data]


class _SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str, dim: int = 1024) -> None:
        self._model_name = model_name
        self._dim = dim
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self._model = SentenceTransformer(self._model_name)
            except ImportError:
                try:
                    from fastembed import TextEmbedding  # type: ignore
                    self._model = TextEmbedding(model_name=self._model_name)
                except ImportError:
                    raise LLMNotConfigured(
                        "Sentence transformers library is not installed. "
                        "Install it via: pip install sentence-transformers"
                    )
        return self._model

    @property
    def provider_name(self) -> str:
        return "sentence_transformers"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, texts):
        import asyncio
        model = self._get_model()
        loop = asyncio.get_event_loop()
        if hasattr(model, "encode"):
            embeddings = await loop.run_in_executor(
                None, lambda: model.encode(texts, normalize_embeddings=True).tolist()
            )
            return embeddings
        elif hasattr(model, "embed"):
            generator = model.embed(texts)
            return [e.tolist() for e in generator]
        return []


def get_llm_provider() -> BaseLLMProvider:
    settings = get_settings()
    if not settings.llm_configured:
        raise LLMNotConfigured(
            "LLM is not configured. Set LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY. "
            "Non-LLM APIs remain fully operational."
        )
    provider = (settings.LLM_PROVIDER or "").lower()
    if provider == "openai":
        return _OpenAIProvider(settings.LLM_MODEL, settings.LLM_API_KEY)
    elif provider == "groq":
        return _OpenAIProvider(
            settings.LLM_MODEL,
            settings.LLM_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    elif provider == "google":
        return _GoogleProvider(settings.LLM_MODEL, settings.LLM_API_KEY)
    raise LLMNotConfigured(
        f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. Supported: openai, groq, google."
    )


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if not settings.embedding_configured:
        raise LLMNotConfigured(
            "Embedding provider not configured. Set EMBEDDING_PROVIDER and EMBEDDING_MODEL."
        )
    provider = (settings.EMBEDDING_PROVIDER or "").lower()
    dim = settings.effective_embedding_dim
    if provider in ("sentence_transformers", "sentence-transformers"):
        return _SentenceTransformersEmbeddingProvider(
            settings.EMBEDDING_MODEL or "BAAI/bge-m3", dim=dim
        )
    elif provider == "openai":
        return _OpenAIEmbeddingProvider(
            settings.EMBEDDING_MODEL, settings.EMBEDDING_API_KEY, dim
        )
    raise LLMNotConfigured(
        f"Unknown EMBEDDING_PROVIDER '{settings.EMBEDDING_PROVIDER}'. "
        "Supported: sentence_transformers, openai."
    )
