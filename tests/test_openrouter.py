"""Unit tests for the OpenRouter async streaming client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from remmeh.api import (
    NetworkError,
    OpenRouterClient,
    OpenRouterError,
    RateLimitError,
    TimeoutError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_KEY = "sk-or-test-key"
MODEL = "anthropic/claude-3.5-sonnet"
MESSAGES = [{"role": "user", "content": "Hello"}]


def _make_sse_lines(tokens: list[str], include_done: bool = True) -> list[str]:
    """Build realistic SSE lines from a list of token strings."""
    lines = []
    for token in tokens:
        data = {"choices": [{"delta": {"content": token}}]}
        lines.append(f"data: {json.dumps(data)}")
    if include_done:
        lines.append("data: [DONE]")
    return lines


async def aiter_from_list(items: list[str]):
    """Yield items one by one as an async iterator."""
    for item in items:
        yield item


async def _collect_tokens(client: OpenRouterClient, messages: list[dict], model: str) -> list[str]:
    """Collect all yielded tokens from stream_chat into a list."""
    return [token async for token in client.stream_chat(messages, model)]


def _make_stream_mock(mocker, response: MagicMock) -> MagicMock:
    """Create a mock for httpx.AsyncClient used as a context manager with .stream().

    The implementation uses:
        async with httpx.AsyncClient(...) as http_client:
            async with http_client.stream(...) as response:

    We patch `httpx.AsyncClient` at the module level so the constructor returns
    a context manager that yields `mock_http_client`, whose `.stream()` returns
    a context manager that yields `response`.
    """
    mock_http_client = MagicMock()
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_http_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)
    return mock_http_client


def _make_ok_response(lines: list[str]) -> MagicMock:
    """Build a mock 200 response with the given SSE lines."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    async def _aiter_lines():
        for line in lines:
            yield line

    mock_response.aiter_lines = _aiter_lines
    return mock_response


def _make_error_response(status_code: int, body: str = "Error") -> MagicMock:
    """Build a mock error response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.aread = AsyncMock(return_value=body.encode())
    return mock_response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> OpenRouterClient:
    """A client instance with a fake API key."""
    return OpenRouterClient(api_key=API_KEY)


# ---------------------------------------------------------------------------
# Streaming happy-path tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_chat_yields_tokens(client: OpenRouterClient, mocker) -> None:
    """stream_chat yields each delta content string from the SSE response."""
    lines = _make_sse_lines(["Hello", " world"])
    response = _make_ok_response(lines)
    _make_stream_mock(mocker, response)

    tokens = await _collect_tokens(client, MESSAGES, MODEL)
    assert tokens == ["Hello", " world"]


@pytest.mark.asyncio
async def test_stream_chat_skips_done_marker(client: OpenRouterClient, mocker) -> None:
    """stream_chat silently consumes 'data: [DONE]' without yielding."""
    lines = _make_sse_lines(["token"], include_done=True)
    response = _make_ok_response(lines)
    _make_stream_mock(mocker, response)

    tokens = await _collect_tokens(client, MESSAGES, MODEL)
    assert "[DONE]" not in tokens
    assert tokens == ["token"]


@pytest.mark.asyncio
async def test_stream_chat_skips_empty_delta(client: OpenRouterClient, mocker) -> None:
    """stream_chat skips SSE lines where delta content is None or empty string."""
    lines = [
        'data: {"choices":[{"delta":{"content":""}}]}',
        'data: {"choices":[{"delta":{}}]}',
        'data: {"choices":[{"delta":{"content":"real"}}]}',
        "data: [DONE]",
    ]
    response = _make_ok_response(lines)
    _make_stream_mock(mocker, response)

    tokens = await _collect_tokens(client, MESSAGES, MODEL)
    assert tokens == ["real"]


@pytest.mark.asyncio
async def test_stream_chat_skips_non_data_lines(client: OpenRouterClient, mocker) -> None:
    """stream_chat ignores SSE comment/event/retry lines (not prefixed with 'data: ')."""
    lines = [
        ": keep-alive",
        'data: {"choices":[{"delta":{"content":"hi"}}]}',
        "data: [DONE]",
    ]
    response = _make_ok_response(lines)
    _make_stream_mock(mocker, response)

    tokens = await _collect_tokens(client, MESSAGES, MODEL)
    assert tokens == ["hi"]


# ---------------------------------------------------------------------------
# Error classification tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_chat_rate_limit_raises_rate_limit_error(
    client: OpenRouterClient, mocker
) -> None:
    """HTTP 429 response raises RateLimitError."""
    response = _make_error_response(429, "Too Many Requests")
    _make_stream_mock(mocker, response)

    with pytest.raises(RateLimitError) as exc_info:
        await _collect_tokens(client, MESSAGES, MODEL)

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_stream_chat_server_error_raises_openrouter_error(
    client: OpenRouterClient, mocker
) -> None:
    """HTTP 500 response raises OpenRouterError (not RateLimitError)."""
    response = _make_error_response(500, "Internal Server Error")
    _make_stream_mock(mocker, response)

    with pytest.raises(OpenRouterError) as exc_info:
        await _collect_tokens(client, MESSAGES, MODEL)

    assert exc_info.value.status_code == 500
    assert not isinstance(exc_info.value, RateLimitError)


@pytest.mark.asyncio
async def test_stream_chat_client_error_raises_openrouter_error(
    client: OpenRouterClient, mocker
) -> None:
    """HTTP 401 response raises OpenRouterError with status_code set."""
    response = _make_error_response(401, "Unauthorized")
    _make_stream_mock(mocker, response)

    with pytest.raises(OpenRouterError) as exc_info:
        await _collect_tokens(client, MESSAGES, MODEL)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_stream_chat_timeout_raises_timeout_error(client: OpenRouterClient, mocker) -> None:
    """httpx.TimeoutException raises TimeoutError."""
    mock_http_client = MagicMock()
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_http_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_ctx = MagicMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)
    mocker.patch("httpx.AsyncClient", return_value=mock_client_ctx)

    with pytest.raises(TimeoutError):
        await _collect_tokens(client, MESSAGES, MODEL)


@pytest.mark.asyncio
async def test_stream_chat_timeout_raises_timeout_error(client: OpenRouterClient, mocker) -> None:
    """httpx.TimeoutException raises TimeoutError."""
    mock_http_client = MagicMock()
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_http_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)
    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)

    with pytest.raises(TimeoutError):
        await _collect_tokens(client, MESSAGES, MODEL)


@pytest.mark.asyncio
async def test_stream_chat_connect_error_raises_network_error(
    client: OpenRouterClient, mocker
) -> None:
    """httpx.ConnectError raises NetworkError."""
    mock_http_client = MagicMock()
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_http_client.stream = MagicMock(return_value=mock_stream_ctx)

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)
    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)

    with pytest.raises(NetworkError):
        await _collect_tokens(client, MESSAGES, MODEL)


# ---------------------------------------------------------------------------
# Error hierarchy tests
# ---------------------------------------------------------------------------


def test_rate_limit_error_is_openrouter_error() -> None:
    """RateLimitError should be a subclass of OpenRouterError."""
    err = RateLimitError("rate limited", status_code=429)
    assert isinstance(err, OpenRouterError)
    assert err.status_code == 429


def test_timeout_error_is_openrouter_error() -> None:
    """TimeoutError should be a subclass of OpenRouterError."""
    err = TimeoutError("timed out")
    assert isinstance(err, OpenRouterError)


def test_network_error_is_openrouter_error() -> None:
    """NetworkError should be a subclass of OpenRouterError."""
    err = NetworkError("connection refused")
    assert isinstance(err, OpenRouterError)


def test_openrouter_error_stores_status_code() -> None:
    """OpenRouterError stores status_code attribute."""
    err = OpenRouterError("bad request", status_code=400)
    assert err.status_code == 400
    assert str(err) == "bad request"


def test_openrouter_error_status_code_optional() -> None:
    """OpenRouterError can be created without status_code."""
    err = OpenRouterError("generic error")
    assert err.status_code is None


# ---------------------------------------------------------------------------
# Request validation tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_chat_sends_correct_headers(client: OpenRouterClient, mocker) -> None:
    """stream_chat sends Authorization, HTTP-Referer, and X-Title headers."""
    lines = _make_sse_lines(["hi"])
    response = _make_ok_response(lines)
    mock_http_client = _make_stream_mock(mocker, response)

    await _collect_tokens(client, MESSAGES, MODEL)

    call_kwargs = mock_http_client.stream.call_args
    headers = call_kwargs.kwargs.get("headers", {})
    assert headers.get("Authorization") == f"Bearer {API_KEY}"
    assert "HTTP-Referer" in headers
    assert "X-Title" in headers


@pytest.mark.asyncio
async def test_stream_chat_sends_correct_body(client: OpenRouterClient, mocker) -> None:
    """stream_chat sends model, messages, and stream=True in request body."""
    lines = _make_sse_lines(["hi"])
    response = _make_ok_response(lines)
    mock_http_client = _make_stream_mock(mocker, response)

    await _collect_tokens(client, MESSAGES, MODEL)

    call_kwargs = mock_http_client.stream.call_args
    json_body = call_kwargs.kwargs.get("json", {})
    assert json_body.get("model") == MODEL
    assert json_body.get("messages") == MESSAGES
    assert json_body.get("stream") is True
