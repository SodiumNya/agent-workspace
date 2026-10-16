import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator
) 

from app.llm.base import StreamingLLMClient
from app.llm.factory import create_llm_client
from app.llm.schemas import RequestStatus
from app.prompts.meeting import build_user_prompt, SYSTEM_PROMPR

app = FastAPI(title="meeting agent")
logger = logging.getLogger(__name__)

class MeetingSummaryRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True
    )

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="待整理的会议纪要文本",
        examples=[
            "今天的会议纪要内容是..."
        ]
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("会议纪要不能为空或纯空格")

        if len(value) > 10_000:
            raise ValueError("会议纪要不能超过10000字符")

        return value
    
class MeetingSummaryResponse(BaseModel):
    summary: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/meeting-summary")
def meeting_summary(request: MeetingSummaryRequest):

    # 构造prompt
    meeting_content = request.text
    prompt = build_user_prompt(meeting_content)
    # 发送请求
    llm_client = create_llm_client(mode="sdk")
    result = llm_client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPR)

    if result.status != RequestStatus.SUCCESS:
        raise HTTPException(status_code=502, detail="模型服务未能完成会议整理")

    if not result.content or not result.content.strip():
        raise HTTPException(status_code=502, detail="模型未返回有效内容")
    response = MeetingSummaryResponse(summary=result.content)
    return response

@app.post("/meeting-summary/stream")
def meeting_summary_stream(request: MeetingSummaryRequest):

    prompt = build_user_prompt(request.text)

    def event_stream():
        has_text = False

        try:
            llm_client = create_llm_client(mode="sdk")

            if not isinstance(llm_client, StreamingLLMClient):
                raise HTTPException(status_code=500, detail="模型客户端不支持流式输出")

            for chunk in llm_client.generate_stream(prompt=prompt, system_prompt=SYSTEM_PROMPR):

                if not chunk:
                    continue

                if chunk.strip():
                    has_text = True
                yield json.dumps(
                    {
                        "type": "delta",
                        "text": chunk
                    },
                    ensure_ascii=False,
                ) + "\n"

        except Exception:

            logger.exception("Error during streaming response")

            yield json.dumps(
                {"type": "error", "message": "模型服务暂时不可用"},
                ensure_ascii=False,
            ) + "\n"
            return

        if not has_text:
            yield json.dumps(
                {"type": "error", "message": "模型未返回有效内容"},
                ensure_ascii=False,
            ) + "\n"
            return

        yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
    )