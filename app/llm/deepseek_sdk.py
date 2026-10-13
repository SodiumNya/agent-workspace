import os
import logging
from app.llm.base import LLMClient
from app.llm.schemas import LLMResult, RequestStatus
from openai import (
    OpenAI,
    APIError,
    APIStatusError,
    APIConnectionError,
    APITimeoutError,
    )

class DeepSeekClient(LLMClient):

    def __init__(self, model, api_key):

        self.model = model
        self.api_key = api_key

        self.logger = logging.getLogger(__name__)

    def generate(self, prompt, system_prompt):

        base_url = os.getenv("DSK_BASE_URL")
        if base_url is None or base_url.strip() == "":
            raise ValueError("base url is None or blank!")
        
        client = OpenAI(
            api_key=self.api_key,
              base_url=base_url,
              timeout=120.0,
              max_retries=1
        )

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=False,
                extra_body={"thinking": {"type": "disabled"}}
            )

            if not response.choices:
                return LLMResult(
                    status=RequestStatus.FAILED,
                    error="model did not return candidate result!"
                )

            content = response.choices[0].message.content

            if not content or not content.strip():
                return LLMResult(
                    status=RequestStatus.FAILED,
                    error="model did not return valid text"
                )

            return LLMResult(
                status=RequestStatus.SUCCESS,
                content=content
            )

        except APITimeoutError:
            self.logger.warning("DeepSeek request timeout")

            return LLMResult(
                status=RequestStatus.UNKNOWN,
                error="Model request timed out, and the remote execution status is unknown",
            )
        except APIConnectionError as exc:
            self.logger.warning(
                "DeepSeek network error: %s",
                type(exc).__name__,
            )

            return LLMResult(
                status=RequestStatus.UNKNOWN,
                error="Model service network connection failed"
            )
        except APIStatusError as exc:
            code = exc.status_code

            self.logger.warning(
                "DeepSeek API Exception: status=%s",
                code
            )

            if code == 402:
                message = "DeepSeek 账户余额不足"

            elif code == 429:
                message = "请求过于频繁，已达到速率限制"

            elif code in (401, 403):
                message = "API Key 无效或没有访问权限"

            elif code == 404:
                message = "模型不存在或当前不可用"

            elif code >= 500:
                message = "DeepSeek 服务端异常"

            else:
                message = f"DeepSeek API 错误: {code}"

            status = (
                RequestStatus.UNKNOWN
                if code in (408, 500, 502, 503, 504)
                else RequestStatus.FAILED
            )

            return LLMResult(
                status=status,
                error=message,
                error_code=code,
            )
        except APIError as exc:
            self.logger.exception(
                "DeepSeek SDK exception"
            )

            return LLMResult(
                status=RequestStatus.UNKNOWN,
                error=f"SDK exception: {type(exc).__name__}",
            )