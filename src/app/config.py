"""App configuration loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    google_credentials_path: str
    google_drive_folder_id: str | None
    es_url: str
    es_index: str
    es_user: str | None
    es_password: str | None
    es_verify_certs: bool
    es_ca_cert: str | None
    api_host: str
    api_port: int


    @staticmethod
    def from_env() -> "Settings":
        creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "").strip() or None
        es_url = os.environ.get("ES_URL", "http://localhost:9200").strip()
        es_index = os.environ.get("ES_INDEX", "drive_files").strip()
        es_user = os.environ.get("ES_USER", "").strip() or None
        es_password = os.environ.get("ES_PASSWORD", "").strip() or None
        es_verify_certs = os.environ.get("ES_VERIFY_CERTS", "true").strip().lower() == "true"
        es_ca_cert = os.environ.get("ES_CA_CERT", "").strip() or None
        api_host = os.environ.get("API_HOST", "127.0.0.1").strip()
        api_port = int(os.environ.get("API_PORT", "8000"))

        if not creds:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required for Google Drive")
        if not Path(creds).exists():
            raise FileNotFoundError(f"Service account JSON not found: {creds}")

        return Settings(
            google_credentials_path=creds,
            google_drive_folder_id=folder_id,
            es_url=es_url,
            es_index=es_index,
            es_user=es_user,
            es_password=es_password,
            es_verify_certs=es_verify_certs,
            es_ca_cert=es_ca_cert,
            api_host=api_host,
            api_port=api_port,
        )
