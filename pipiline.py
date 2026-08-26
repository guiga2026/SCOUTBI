"""Manual ETL entry point used by Docker and local development."""

import argparse

from sports_bi.etl.sync import sync_brazilian_competitions, sync_league_season
from sports_bi.services.football_api import FootballAPI


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza dados de futebol para o Sports BI")
    parser.add_argument("--competition", default=None, help="Nome da competição brasileira, por exemplo Serie B")
    parser.add_argument("--season", type=int, default=None, help="Ano da temporada")
    args = parser.parse_args()

    api = FootballAPI()
    rows = api.competitions()
    synced = sync_brazilian_competitions(api)
    print(f"Competições brasileiras descobertas e sincronizadas: {synced}", flush=True)
    if args.competition is None and args.season is None:
        return
    if not args.competition or args.season is None:
        parser.error("--competition e --season devem ser usados juntos")
    target = next((item for item in rows if (item.get("league") or {}).get("name", "").casefold() == args.competition.casefold()), None)
    if target is None:
        parser.error(f"Competição não encontrada no Brasil: {args.competition}")
    league_id = (target.get("league") or {}).get("id")
    result = sync_league_season(league_id, args.season, api)
    print(f"{args.competition} {args.season}: temporada={result['season']}, times={result['teams']}, jogos={result['fixtures']}", flush=True)


if __name__ == "__main__":
    main()