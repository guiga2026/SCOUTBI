"""Manual ETL entry point used by Docker and local development."""

from sports_bi.etl.sync import sync_brazilian_competitions


if __name__ == "__main__":
    print(f"Competições sincronizadas: {sync_brazilian_competitions()}", flush=True)