import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

with patch("dotenv.load_dotenv"):
    from app import api

from app.prompts.meeting import SYSTEM_PROMPR, build_user_prompt

TEXT = "小王周五前完成模型调用，前端展示方案尚未确定。"


class FakeStreamingClient:
    def __init__(self, chunks=(), error_before=False, error_after=False):
        self.chunks = chunks
        self.error_before = error_before
        self.error_after = error_after
        self.call = None

    def generate_stream(self, prompt, system_prompt):
        self.call = (prompt, system_prompt)
        if self.error_before:
            raise RuntimeError("raw upstream failure")

        yield from self.chunks

        if self.error_after:
            raise RuntimeError("raw upstream failure")


@pytest.fixture
def stream_api(monkeypatch):
    model = FakeStreamingClient()
    factory = Mock(return_value=model)
    monkeypatch.setattr(api, "create_llm_client", factory)

    with TestClient(api.app) as client:
        yield client, factory, model


def parse_events(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    return [json.loads(line) for line in response.text.splitlines()]


def test_stream_success_ends_with_one_done(stream_api):
    client, factory, model = stream_api
    model.chunks = ["摘要：", "完成模型调用。"]

    response = client.post("/meeting-summary/stream", json={"text": TEXT})
    events = parse_events(response)

    assert events == [
        {"type": "delta", "text": "摘要："},
        {"type": "delta", "text": "完成模型调用。"},
        {"type": "done"},
    ]
    factory.assert_called_once_with(mode="sdk")
    assert model.call == (build_user_prompt(TEXT), SYSTEM_PROMPR)


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": " \t\n "}])
def test_stream_invalid_input_does_not_create_client(stream_api, payload):
    client, factory, _ = stream_api

    response = client.post("/meeting-summary/stream", json=payload)

    assert response.status_code == 422
    factory.assert_not_called()


def test_stream_without_text_emits_error_without_done(stream_api):
    client, _, model = stream_api
    model.chunks = []

    events = parse_events(client.post("/meeting-summary/stream", json={"text": TEXT}))

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert not any(event["type"] == "done" for event in events)


def test_stream_whitespace_only_emits_error_without_done(stream_api):
    client, _, model = stream_api
    model.chunks = [" \t\n "]

    events = parse_events(client.post("/meeting-summary/stream", json={"text": TEXT}))

    assert events[-1]["type"] == "error"
    assert not any(event["type"] == "done" for event in events)


@pytest.mark.parametrize(
    ("error_before", "error_after", "chunks", "expected_types"),
    [
        (True, False, [], ["error"]),
        (False, True, ["摘要："], ["delta", "error"]),
    ],
)
def test_stream_upstream_failure_emits_one_sanitized_error(
    stream_api, error_before, error_after, chunks, expected_types
):
    client, _, model = stream_api
    model.error_before = error_before
    model.error_after = error_after
    model.chunks = chunks

    response = client.post("/meeting-summary/stream", json={"text": TEXT})
    events = parse_events(response)

    assert [event["type"] for event in events] == expected_types
    assert sum(event["type"] == "error" for event in events) == 1
    assert not any(event["type"] == "done" for event in events)
    assert "raw upstream failure" not in response.text