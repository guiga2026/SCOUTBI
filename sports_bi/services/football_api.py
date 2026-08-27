import time
from typing import Any

import httpx

from sports_bi.app.config import get_settings
from sports_bi.services.cache import RedisCache


class FootballAPIError(RuntimeError):
    pass


class FootballAPI:
    def __init__(self, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        if not settings.api_football_key:
            raise FootballAPIError("API_FOOTBALL_KEY não configurada")
        self.client = client or httpx.Client(base_url=settings.api_football_base_url, timeout=settings.api_timeout_seconds)
        self.client.headers["x-apisports-key"] = settings.api_football_key
        self.cache = RedisCache(settings.redis_url) if settings.redis_cache_enabled else None

    def get(self, endpoint: str, **params: Any) -> list[dict[str, Any]]:
        settings = get_settings()
        clean_params = {key: value for key, value in params.items() if value is not None}
        if self.cache:
            try:
                cached = self.cache.get(endpoint, clean_params)
                if cached is not None:
                    return cached
                if not self.cache.consume_quota(settings.api_daily_request_limit):
                    raise FootballAPIError("Limite diário configurado para a API-Football atingido")
            except FootballAPIError:
                raise
            except Exception:
                pass
        response: httpx.Response | None = None
        for attempt in range(settings.api_max_retries + 1):
            response = self.client.get(endpoint, params=clean_params)
            if response.status_code not in (429, 500, 502, 503, 504) or attempt == settings.api_max_retries:
                break
            time.sleep(2**attempt)
        assert response is not None
        if response.status_code in (401, 403):
            raise FootballAPIError(f"API-Football rejeitou a autenticação ({response.status_code})")
        if response.status_code == 429:
            raise FootballAPIError("Limite de requisições da API-Football atingido")
        response.raise_for_status()
        payload = response.json()
        errors = payload.get("errors") or {}
        if errors:
            raise FootballAPIError(f"API-Football retornou erros: {errors}")
        result = payload.get("response", [])
        if self.cache:
            try:
                self.cache.set(endpoint, clean_params, result)
            except Exception:
                pass
        return result

    def competitions(self, country: str | None = None) -> list[dict[str, Any]]:
        return self.get("/leagues", country=country)

    def seasons(self, league_id: int) -> list[dict[str, Any]]:
        rows = self.get("/leagues", id=league_id)
        return rows[0].get("seasons", []) if rows else []

    def teams(self, league_id: int, season: int) -> list[dict[str, Any]]:
        return self.get("/teams", league=league_id, season=season)

    def fixtures(self, league_id: int, season: int) -> list[dict[str, Any]]:
        return self.get("/fixtures", league=league_id, season=season)

    def events(self, fixture_id: int) -> list[dict[str, Any]]:
        return self.get("/fixtures/events", fixture=fixture_id)

    def statistics(self, fixture_id: int) -> list[dict[str, Any]]:
        return self.get("/fixtures/statistics", fixture=fixture_id)

    def standings(self, league_id: int, season: int) -> list[dict[str, Any]]:
        return self.get("/standings", league=league_id, season=season)

    def lineups(self, fixture_id: int) -> list[dict[str, Any]]:
        return self.get("/fixtures/lineups", fixture=fixture_id)

    def player_statistics(self, player_id: int, league_id: int, season: int) -> list[dict[str, Any]]:
        return self.get("/players", id=player_id, league=league_id, season=season)

    def transfers(self, player_id: int) -> list[dict[str, Any]]:
        return self.get("/transfers", player=player_id)

    def injuries(self, league_id: int, season: int) -> list[dict[str, Any]]:
        return self.get("/injuries", league=league_id, season=season)

