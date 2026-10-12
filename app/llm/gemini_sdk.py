import logging
from google import genai
from app.llm.base import LLMClient
from google.genai import types, errors
from app.llm.schemas import LLMResult, RequestStatus

class GeminiSDKClient(LLMClient):

    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(
            api_key=api_key,
        )
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate(self, prompt, system_prompt):
        try:
            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt,
                system_instruction=system_prompt
            )
            if interaction.output_text is None or interaction.output_text.strip() == "":
                return LLMResult(
                    status=RequestStatus.FAILED,
                    error="The model did not return usable text!"
                )
            return LLMResult(
                status=RequestStatus.SUCCESS,
                content=interaction.output_text
            )
        except errors.APIError as exc:
            self.logger.warning(
                "Gemini network error: %s",
                type(exc).__name__,
            )

            return LLMResult(
                status=RequestStatus.UNKNOWN,
                error=f"network exception: {type(exc).__name__}",
            )

