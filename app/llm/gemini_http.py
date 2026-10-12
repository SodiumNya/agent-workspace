import os
import httpx
import logging
import random
import time
from app.llm.base import LLMClient
from app.llm.schemas import LLMResult, RequestStatus


class GeminiHttpClient(LLMClient):

    RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

    def __init__(self, api_key:str, model:str):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)

        self.max_attempts = 5

        self.base_url = os.getenv("GEMINI_BASE_URL")
        if not self.base_url: 
            raise ValueError("gemini base url not founod!")
        
        self.client = httpx.Client(
            base_url=self.base_url,
        )

    def generate(self, prompt, system_prompt):

        path = (
            f"v1beta/models/{self.model}"
            ":interactions"
        )

        payload = {
            "model": self.model,
            "systemInstruction": system_prompt,
            "input": prompt
        }

        for attempt in range(1, self.max_attempts + 1):
            try: 
                response = self.client.post(
                    path,
                    headers={
                        "x-goog-api-key": self.api_key
                    },
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()
                candidates = data.get("candidates", [])

                if not candidates:
                    return LLMResult(
                        status=RequestStatus.FAILED,
                        error="model did not return candidates results!",
                    )

                content = candidates[0].get('content', {})
                parts = content.get("parts", [])

                answer = "".join(
                    part.get("text", "")
                    for part in parts
                    if isinstance(part, dict)
                    and isinstance(part.get("text"), str)
                )    

                if not answer:
                    return LLMResult(
                        status=RequestStatus.FAILED,
                        error="model did not return content!",
                    )            

                return LLMResult(
                    status=RequestStatus.SUCCESS,
                    content=answer,
                )
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code

                self.logger.warning(
                    "Gemini HTTP error: %s, attempt=%s",
                    code, 
                    attempt
                )

                should_retry = code in self.RETRYABLE_STATUS

                if should_retry and attempt < self.max_attempts:
                    self._backoff(attempt)
                    continue

                status = (
                    RequestStatus.UNKNOWN
                    if code in {408, 500, 502, 503, 504}
                    else RequestStatus.FAILED
                )

                return LLMResult(
                    status=status,
                    error=f"HTTP {code}: API request failed!",
                    error_code=code
                )
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError
            ) as exc:

                self.logger.warning(
                    "Network error: %s, attempt=%s",
                    type(exc).__name__,
                    attempt,
                )
                if attempt < self.max_attempts:
                    self._backoff(attempt)
                    continue

                return LLMResult(
                    status=RequestStatus.UNKNOWN,
                    error=f"network exception: {type(exc).__name__}",
                )
            except (ValueError, KeyError, TypeError) as exc:
                self.logger.error(
                    "Invalid response: %s",
                    type(exc).__name__,
                )

                return LLMResult(
                    status=RequestStatus.UNKNOWN,
                    error="Abnormal model response format",
                )

        return LLMResult(
            status=RequestStatus.UNKNOWN,
            error="The request did not yield a definite result",
        )

    @staticmethod
    def _backoff(attempt: int):
        delay = min(2 ** (attempt - 1), 8)
        delay += random.uniform(0, 0.5)
        time.sleep(delay)

    def close(self):
        self.client.close()