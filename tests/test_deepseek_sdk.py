from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.llm.deepseek_sdk import DeepSeekClient


def test_generate_stream_yields_text_and_closes_resources(monkeypatch):
    monkeypatch.setenv("DSK_BASE_URL", "https://example.invalid")

    chunks = [
        SimpleNamespace(choices=[]),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=None), finish_reason=None
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="摘要："), finish_reason=None
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(delta=SimpleNamespace(content=" "), finish_reason=None)
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="完成模型调用。"),
                    finish_reason="stop",
                )
            ]
        ),
    ]
    stream = MagicMock()
    stream.__iter__.return_value = iter(chunks)
    stream_context = MagicMock()
    stream_context.__enter__.return_value = stream

    client = MagicMock()
    client.chat.completions.create.return_value = stream_context
    client_context = MagicMock()
    client_context.__enter__.return_value = client

    with patch(
        "app.llm.deepseek_sdk.OpenAI", return_value=client_context
    ) as openai_factory:
        deepseek_client = DeepSeekClient(model="test-model", api_key="test-key")

        result = list(deepseek_client.generate_stream("prompt", "system"))

    assert result == ["摘要：", " ", "完成模型调用。"]
    assert client.chat.completions.create.call_args.kwargs["stream"] is True
    stream_context.__exit__.assert_called_once()
    client_context.__exit__.assert_called_once()
    openai_factory.assert_called_once()


def test_generate_stream_rejects_whitespace_only_output(monkeypatch):
    monkeypatch.setenv("DSK_BASE_URL", "https://example.invalid")

    chunks = [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=" \t\n "),
                    finish_reason="stop",
                )
            ]
        )
    ]
    stream = MagicMock()
    stream.__iter__.return_value = iter(chunks)
    stream_context = MagicMock()
    stream_context.__enter__.return_value = stream

    client = MagicMock()
    client.chat.completions.create.return_value = stream_context
    client_context = MagicMock()
    client_context.__enter__.return_value = client

    with patch("app.llm.deepseek_sdk.OpenAI", return_value=client_context):
        deepseek_client = DeepSeekClient(model="test-model", api_key="test-key")

        with pytest.raises(RuntimeError, match="without yielding any text"):
            list(deepseek_client.generate_stream("prompt", "system"))

    stream_context.__exit__.assert_called_once()
    client_context.__exit__.assert_called_once()


def test_generate_stream_raises_when_output_is_length_limited(monkeypatch):
    monkeypatch.setenv("DSK_BASE_URL", "https://example.invalid")

    chunks = [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="部分结果"),
                    finish_reason=None,
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=None),
                    finish_reason="length",
                )
            ]
        ),
    ]
    stream = MagicMock()
    stream.__iter__.return_value = iter(chunks)
    stream_context = MagicMock()
    stream_context.__enter__.return_value = stream

    client = MagicMock()
    client.chat.completions.create.return_value = stream_context
    client_context = MagicMock()
    client_context.__enter__.return_value = client

    with patch("app.llm.deepseek_sdk.OpenAI", return_value=client_context):
        deepseek_client = DeepSeekClient(model="test-model", api_key="test-key")
        generated = deepseek_client.generate_stream("prompt", "system")

        assert next(generated) == "部分结果"
        with pytest.raises(RuntimeError, match="length"):
            next(generated)

    stream_context.__exit__.assert_called_once()
    client_context.__exit__.assert_called_once()