from abc import ABC, abstractmethod
from collections.abc import Iterator
from app.llm.schemas import LLMResult
from typing import Protocol, runtime_checkable

class LLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> LLMResult:
        pass


@runtime_checkable
class StreamingLLMClient(Protocol):
    def generate_stream(
        self, prompt: str, system_prompt: str
    ) -> Iterator[str]:
        ...