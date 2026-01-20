"""CLI entrypoint to sync Elasticsearch with Google Drive."""

from __future__ import annotations

import logging

from app.config import Settings
from app.google_drive_client import GoogleDriveClient
from app.indexer import DocumentIndexer
from app.logging_config import configure_logging
from app.utils import build_es_client


configure_logging()
LOGGER = logging.getLogger(__name__)


def main() -> None:
    settings = Settings.from_env()
    es = build_es_client(
        settings.es_url,
        settings.es_user,
        settings.es_password,
        settings.es_verify_certs,
        settings.es_ca_cert,
    )
    drive_client = GoogleDriveClient(
        settings.google_credentials_path,
        settings.google_drive_folder_id,
    )
    indexer = DocumentIndexer(drive_client, es, settings.es_index)
    summary = indexer.sync()
    LOGGER.info("Sync complete: %s", summary)


if __name__ == "__main__":
    main()
