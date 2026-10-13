"""Day 3 核心验收，全部使用假模型。"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# factory 导入时会读取 .env，测试中跳过。
with patch("dotenv.load_dotenv"):
    from app import api

from app.llm.schemas import LLMResult, RequestStatus
from app.prompts.meeting import SYSTEM_PROMPR, build_user_prompt

TEXT = "小王周五前完成模型调用，前端展示方案尚未确定。"
SUMMARY = "摘要：讨论模型调用。待办：小王周五前完成。待确认：前端展示方案。"


@pytest.fixture
def setup_api(monkeypatch):
    model = Mock()
    model.generate.return_value = LLMResult(RequestStatus.SUCCESS, content=SUMMARY)
    factory = Mock(return_value=model)
    # 替换接口实际使用的工厂，避免调用真实模型。
    monkeypatch.setattr(api, "craeate_llm_client", factory)
    with TestClient(api.app) as client:
        yield client, factory, model


def check_call(factory, model):
    factory.assert_called_once_with(mode="sdk")
    model.generate.assert_called_once_with(
        prompt=build_user_prompt(TEXT), system_prompt=SYSTEM_PROMPR
    )


def check_502(response):
    assert response.status_code == 502
    detail = response.json().get("detail")
    assert isinstance(detail, str) and detail.strip()


def test_success(setup_api):
    client, factory, model = setup_api
    response = client.post("/meeting-summary", json={"text": f"  {TEXT}\n"})
    check_call(factory, model)
    assert response.status_code == 200
    assert response.json() == {"summary": SUMMARY}


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": " \t\n "}])
def test_invalid_input(setup_api, payload):
    client, factory, model = setup_api
    response = client.post("/meeting-summary", json=payload)
    assert response.status_code == 422
    factory.assert_not_called()
    model.generate.assert_not_called()


@pytest.mark.parametrize("status", [RequestStatus.FAILED, RequestStatus.UNKNOWN])
def test_model_failure(setup_api, status):
    client, factory, model = setup_api
    model.generate.return_value = LLMResult(status, error="模型服务暂时不可用")
    response = client.post("/meeting-summary", json={"text": TEXT})
    check_call(factory, model)
    check_502(response)


@pytest.mark.parametrize("content", [None, "", " \t\n "])
def test_empty_answer(setup_api, content):
    client, factory, model = setup_api
    model.generate.return_value = LLMResult(RequestStatus.SUCCESS, content=content)
    response = client.post("/meeting-summary", json={"text": TEXT})
    check_call(factory, model)
    check_502(response)
