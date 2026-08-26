"""Manual ETL entry point used by Docker and local development."""

from sports_bi.etl.sync import sync_brazilian_competitions


if __name__ == "__main__":
    sync_brazilian_competitions()