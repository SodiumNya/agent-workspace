from abc import ABC, abstractmethod
from app.llm.schemas import LLMResult

class LLMClient(ABC):

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> LLMResult:
        pass
    