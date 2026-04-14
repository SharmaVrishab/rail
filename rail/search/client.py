"""HTTP client with rate limiting, retries, and optional API key injection.

Provides a shared session used by all search modules. Supports:
- Rate limiting (5 req/sec by default, configurable)
- Automatic retries with exponential backoff
- Optional API key headers for third-party providers
- Browser impersonation via curl-cffi
"""

import os
from typing import Any

from curl_cffi import requests
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential

_client = None

# Requests per second — keep conservative for NTES
_RATE_LIMIT = int(os.environ.get("RAIL_RATE_LIMIT", "5"))


class Client:
    """HTTP client with rate limiting, retry, and optional API key support."""

    DEFAULT_HEADERS: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
    }

    def __init__(self, api_key: str | None = None, api_provider: str = "ntes"):
        """Initialize client session.

        Args:
            api_key: Optional API key for third-party providers (e.g. RapidAPI).
            api_provider: Provider name — "ntes", "rapidapi", or "railwayapi".
        """
        self.api_provider = api_provider
        self._session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)

        if api_key:
            if api_provider == "rapidapi":
                self._session.headers.update({"X-RapidAPI-Key": api_key})
            else:
                self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def __del__(self):
        """Close session on cleanup."""
        if hasattr(self, "_session"):
            self._session.close()

    @sleep_and_retry
    @limits(calls=_RATE_LIMIT, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a rate-limited GET request with automatic retries.

        Args:
            url: Target URL.
            **kwargs: Passed to requests.get().

        Returns:
            HTTP response object.

        Raises:
            Exception: After all retries are exhausted.
        """
        try:
            response = self._session.get(url, impersonate="chrome", **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            raise Exception(f"GET {url} failed: {e}") from e

    @sleep_and_retry
    @limits(calls=_RATE_LIMIT, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a rate-limited POST request with automatic retries.

        Args:
            url: Target URL.
            **kwargs: Passed to requests.post().

        Returns:
            HTTP response object.

        Raises:
            Exception: After all retries are exhausted.
        """
        try:
            response = self._session.post(url, impersonate="chrome", **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            raise Exception(f"POST {url} failed: {e}") from e


def get_client() -> Client:
    """Return the shared Client singleton, creating it on first call.

    Reads optional environment variables:
    - RAIL_API_KEY: API key for third-party providers.
    - RAIL_API_PROVIDER: "ntes" | "rapidapi" | "railwayapi" (default: "ntes").

    Returns:
        Shared Client instance.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("RAIL_API_KEY")
        api_provider = os.environ.get("RAIL_API_PROVIDER", "ntes")
        _client = Client(api_key=api_key, api_provider=api_provider)
    return _client
