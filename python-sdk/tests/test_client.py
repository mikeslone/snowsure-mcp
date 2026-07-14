"""Tests for snowsure.SnowSureClient using httpx.MockTransport (no network)."""

import json

import httpx
import pytest

from snowsure import SnowSureClient, SnowSureError


def make_client(handler):
    return SnowSureClient(transport=httpx.MockTransport(handler))


def envelope(data, meta=None):
    return httpx.Response(200, json={"meta": meta or {"source": "SnowSure"}, "data": data})


def test_get_resorts_unwraps_data_and_sends_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return envelope([{"name": "Las Leñas", "slug": "las-lenas"}])

    with make_client(handler) as client:
        resorts = client.get_resorts(limit=5, region="south-america", sort="score")

    assert seen["path"] == "/api/v1/resorts"
    assert seen["params"] == {"limit": "5", "region": "south-america", "sort": "score"}
    assert resorts == [{"name": "Las Leñas", "slug": "las-lenas"}]


def test_get_resort_hits_slug_path_and_sets_last_meta():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/resorts/matterhorn-ski-paradise"
        return envelope({"slug": "matterhorn-ski-paradise"}, meta={"timestamp": "t1"})

    with make_client(handler) as client:
        resort = client.get_resort("matterhorn-ski-paradise")
        assert resort["slug"] == "matterhorn-ski-paradise"
        assert client.last_meta == {"timestamp": "t1"}


def test_get_resort_requires_slug():
    with make_client(lambda request: envelope({})) as client:
        with pytest.raises(ValueError):
            client.get_resort("")


def test_get_snow_report_returns_data_object_with_resorts():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/snow-report"
        assert dict(request.url.params) == {"sort": "recent", "limit": "2"}
        return envelope({"resorts": [{"slug": "mt-hutt"}, {"slug": "las-lenas"}]})

    with make_client(handler) as client:
        report = client.get_snow_report(sort="recent", limit=2)

    assert [r["slug"] for r in report["resorts"]] == ["mt-hutt", "las-lenas"]


def test_ask_posts_question_with_default_partner_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/ask"
        body = json.loads(request.content)
        assert body == {
            "question": "how much snow at Zermatt?",
            "partnerId": "chatgpt",
            "format": "markdown",
        }
        assert "x-api-key" not in request.headers
        return envelope({"answer": "22 cm base.", "format": "markdown"})

    with make_client(handler) as client:
        answer = client.ask("how much snow at Zermatt?")

    assert answer["answer"] == "22 cm base."


def test_ask_sends_api_key_header_and_optional_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.headers["x-api-key"] == "sk-test"
        assert body["partnerId"] == "acme"
        assert body["resortSlug"] == "las-lenas"
        assert body["locale"] == "es"
        assert body["format"] == "json"
        return envelope({"answer": "Nieve fresca.", "confidence": "high"})

    client = SnowSureClient(
        api_key="sk-test",
        partner_id="acme",
        transport=httpx.MockTransport(handler),
    )
    with client:
        answer = client.ask("nieve?", resort_slug="las-lenas", locale="es", format="json")

    assert answer["confidence"] == "high"


def test_error_payload_raises_snowsure_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Invalid or missing API key"})

    with make_client(handler) as client:
        with pytest.raises(SnowSureError, match="Invalid or missing API key") as excinfo:
            client.ask("hi")
        assert excinfo.value.status_code == 401


def test_http_error_without_json_body_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream boom")

    with make_client(handler) as client:
        with pytest.raises(SnowSureError):
            client.get_resorts()


def test_missing_data_envelope_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    with make_client(handler) as client:
        with pytest.raises(SnowSureError, match="envelope"):
            client.get_snow_report()
