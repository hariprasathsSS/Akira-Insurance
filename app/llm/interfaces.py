"""LLM provider interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class LLMResponse:
    def __init__(
        self,
        content: str,
        model: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> None:
        self.content = content
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class BaseLLMProvider(ABC):
    """Common interface for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


class EmbeddingProvider(ABC):
    """Common interface for embedding providers."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...
