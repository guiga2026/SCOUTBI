import httpx
import pytest

from sports_bi.services.football_api import FootballAPI, FootballAPIError


def test_client_adds_api_key_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-key")
    from sports_bi.app.config import get_settings

    get_settings.cache_clear()
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"response": []})), base_url="https://test")
    FootballAPI(client)
    assert client.headers["x-apisports-key"] == "test-key"
    get_settings.cache_clear()


def test_client_reports_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-key")
    from sports_bi.app.config import get_settings

    get_settings.cache_clear()
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429)), base_url="https://test")
    with pytest.raises(FootballAPIError, match="Limite"):
        FootballAPI(client).get("/leagues")
    get_settings.cache_clear()