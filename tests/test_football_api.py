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


def test_player_statistics_uses_documented_query_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-key")
    from sports_bi.app.config import get_settings

    get_settings.cache_clear()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"response": []})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://test")
    FootballAPI(client).player_statistics(10, 72, 2024)
    assert requests[0].url.path == "/players"
    assert dict(requests[0].url.params) == {"id": "10", "league": "72", "season": "2024"}
    get_settings.cache_clear()