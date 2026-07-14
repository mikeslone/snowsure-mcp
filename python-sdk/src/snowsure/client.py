"""Typed HTTP client for the SnowSure REST API (https://www.snowsure.ai).

All SnowSure API responses use an envelope of the form::

    {"meta": {...}, "data": ...}

Client methods unwrap the envelope and return the ``data`` payload. The
``meta`` block from the most recent successful call is kept on
``SnowSureClient.last_meta`` for callers who need timestamps/attribution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

__all__ = ["SnowSureClient", "SnowSureError", "DEFAULT_BASE_URL"]

DEFAULT_BASE_URL = "https://www.snowsure.ai"

# Public keyless partner tier for POST /api/v1/ask. Other partner IDs
# require an X-API-Key header (pass api_key= to the client).
DEFAULT_PARTNER_ID = "chatgpt"

_USER_AGENT = "snowsure-python/0.1.0 (+https://github.com/mikeslone/snowsure-mcp)"


class SnowSureError(RuntimeError):
    """Raised when the SnowSure API returns an error response."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class SnowSureClient:
    """Thin, typed wrapper over the SnowSure REST API.

    Usage::

        from snowsure import SnowSureClient

        client = SnowSureClient()
        resorts = client.get_resorts(region="europe", limit=10)
        zermatt = client.get_resort("matterhorn-ski-paradise")
        report = client.get_snow_report(sort="recent")
        answer = client.ask("where is the best powder in the alps right now?")

    Args:
        base_url: API origin. Defaults to ``https://www.snowsure.ai``.
        api_key: Optional partner API key, sent as ``X-API-Key`` on
            ``ask()``. Not required for the public tier.
        partner_id: Partner attribution for ``ask()``. Defaults to
            ``"chatgpt"``, the public keyless tier.
        timeout: Request timeout in seconds (default 30).
        transport: Optional ``httpx.BaseTransport`` (useful for testing
            with ``httpx.MockTransport``).
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        api_key: Optional[str] = None,
        partner_id: str = DEFAULT_PARTNER_ID,
        timeout: float = 30.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.partner_id = partner_id
        self.last_meta: Optional[Dict[str, Any]] = None
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            transport=transport,
        )

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SnowSureClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- endpoints ---------------------------------------------------------

    def get_resorts(
        self,
        *,
        limit: Optional[int] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        sort: Optional[str] = None,
        slugs: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List ski resorts with live conditions and SnowSure scores.

        GET /api/v1/resorts

        Args:
            limit: Max results (API default 100, max 500).
            region: One of ``europe``, ``north-america``, ``asia``,
                ``oceania``, ``south-america``.
            country: Filter by country name (e.g. ``"Switzerland"``).
            sort: ``score`` | ``snowfall`` | ``forecast`` | ``name``.
            slugs: Fetch specific resorts by slug.

        Returns:
            The unwrapped ``data`` list of resort objects.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if region is not None:
            params["region"] = region
        if country is not None:
            params["country"] = country
        if sort is not None:
            params["sort"] = sort
        if slugs:
            params["slugs"] = ",".join(slugs)
        return self._get("/api/v1/resorts", params=params)

    def get_resort(self, slug: str) -> Dict[str, Any]:
        """Full detail for one resort: live conditions, forecasts, webcams.

        GET /api/v1/resorts/{slug}

        Args:
            slug: Canonical lowercase-hyphenated resort slug, e.g.
                ``"matterhorn-ski-paradise"``. Resolve names via
                :meth:`get_resorts` and match on ``name``.

        Returns:
            The unwrapped ``data`` resort object.
        """
        if not slug:
            raise ValueError("slug is required")
        return self._get(f"/api/v1/resorts/{slug}")

    def get_snow_report(
        self,
        *,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Global snow rankings powered by the SnowSure score.

        GET /api/v1/snow-report

        Args:
            sort: ``snowsure`` | ``forecast`` | ``recent`` | ``depth``.
            limit: Max results (API default 50, max 100).
            region: Same region values as :meth:`get_resorts`.

        Returns:
            The unwrapped ``data`` object; ranked resorts are under the
            ``"resorts"`` key.
        """
        params: Dict[str, Any] = {}
        if sort is not None:
            params["sort"] = sort
        if limit is not None:
            params["limit"] = limit
        if region is not None:
            params["region"] = region
        return self._get("/api/v1/snow-report", params=params)

    def ask(
        self,
        question: str,
        *,
        resort_slug: Optional[str] = None,
        locale: Optional[str] = None,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """Ask the SnowSure Answer Engine a natural-language question.

        POST /api/v1/ask

        Args:
            question: The question, e.g. ``"how much snow at Zermatt?"``.
            resort_slug: Optional resort slug to scope the answer.
            locale: ``en`` | ``es`` | ``fr`` | ``de`` | ``it`` | ``ja``.
            format: ``"markdown"`` (default) returns prose under
                ``"answer"``; ``"json"`` returns a structured payload with
                ``answer``, ``intent``, ``scope``, ``confidence`` and an
                ``evidence`` list.

        Returns:
            The unwrapped ``data`` object. ``data["answer"]`` is the
            grounded answer text in both formats.
        """
        if not question:
            raise ValueError("question is required")
        body: Dict[str, Any] = {
            "question": question,
            "partnerId": self.partner_id,
            "format": format,
        }
        if resort_slug is not None:
            body["resortSlug"] = resort_slug
        if locale is not None:
            body["locale"] = locale
        headers = {"X-API-Key": self.api_key} if self.api_key else None
        response = self._http.post("/api/v1/ask", json=body, headers=headers)
        return self._unwrap(response)

    # -- internals ---------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = self._http.get(path, params=params or None)
        return self._unwrap(response)

    def _unwrap(self, response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and "error" in payload:
            raise SnowSureError(str(payload["error"]), status_code=response.status_code)
        if response.status_code >= 400:
            raise SnowSureError(
                f"SnowSure API returned HTTP {response.status_code} for {response.request.url}",
                status_code=response.status_code,
            )
        if not isinstance(payload, dict) or "data" not in payload:
            raise SnowSureError(
                "Unexpected response shape: missing 'data' envelope",
                status_code=response.status_code,
            )
        meta = payload.get("meta")
        self.last_meta = meta if isinstance(meta, dict) else None
        return payload["data"]
