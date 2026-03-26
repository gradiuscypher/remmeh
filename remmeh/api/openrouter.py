"""Async OpenRouter HTTP client with SSE streaming and typed error classification."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx

from remmeh.config import OPENROUTER_BASE_URL

log = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Base error for OpenRouter API failures."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(OpenRouterError):
    """429 Too Many Requests from OpenRouter."""


class TimeoutError(OpenRouterError):
    """Request timed out."""


class NetworkError(OpenRouterError):
    """Connection or network failure."""


class OpenRouterClient:
    """Async HTTP client for the OpenRouter chat completions API."""

    def __init__(self, api_key: str, base_url: str = OPENROUTER_BASE_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def stream_chat(
        self,
        messages: list[dict],
        model: str,
        timeout: float = 60.0,
    ) -> AsyncIterator[str]:
        """Yield text tokens from a streaming chat completion.

        Sends a POST to the OpenRouter chat completions endpoint with stream=True
        and yields each non-empty content delta from the SSE response.

        Args:
            messages: List of chat messages e.g. [{"role": "user", "content": "..."}]
            model: OpenRouter model identifier e.g. "anthropic/claude-3.5-sonnet"
            timeout: Total request timeout in seconds (default 60.0). Connect timeout
                     is always 10 seconds.

        Yields:
            Individual text tokens as strings.

        Raises:
            RateLimitError: on HTTP 429
            TimeoutError: on httpx.TimeoutException
            NetworkError: on httpx.ConnectError
            OpenRouterError: on other HTTP 4xx/5xx errors
        """
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://github.com/remmeh",
            "X-Title": "remmeh",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        http_timeout = httpx.Timeout(timeout, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=http_timeout) as http_client:  # noqa: SIM117
                async with http_client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                ) as response:
                    # Check for HTTP errors before streaming
                    if response.status_code != 200:
                        body = await response.aread()
                        text = body.decode(errors="replace")
                        if response.status_code == 429:
                            raise RateLimitError(
                                f"Rate limit exceeded: {text}",
                                status_code=response.status_code,
                            )
                        raise OpenRouterError(
                            f"HTTP {response.status_code}: {text}",
                            status_code=response.status_code,
                        )

                    # Parse SSE stream line by line
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload_str = line[len("data: ") :]
                        if payload_str == "[DONE]":
                            break
                        try:
                            data = json.loads(payload_str)
                        except json.JSONDecodeError:
                            log.debug("Skipping unparseable SSE line: %s", line)
                            continue

                        content = data.get("choices", [{}])[0].get("delta", {}).get("content")
                        if content:
                            yield content

        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Request timed out: {exc}") from exc
        except httpx.ConnectError as exc:
            raise NetworkError(f"Connection failed: {exc}") from exc
