"""FastAPI application for search."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query

from app.config import Settings
from app.google_drive_client import GoogleDriveClient
from app.indexer import DocumentIndexer
from app.logging_config import configure_logging
from app.search_service import SearchService
from app.utils import build_es_client


configure_logging()
LOGGER = logging.getLogger(__name__)

settings = Settings.from_env()

es = build_es_client(
    settings.es_url,
    settings.es_user,
    settings.es_password,
    settings.es_verify_certs,
    settings.es_ca_cert,
)
search_service = SearchService(es, settings.es_index)

app = FastAPI(title="Drive Search Service", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search")
async def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    try:
        return {"results": search_service.search(q, limit=limit)}
    except Exception as exc:
        LOGGER.exception("Search failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/sync")
async def sync_index():
    try:
        drive_client = GoogleDriveClient(
            settings.google_credentials_path,
            settings.google_drive_folder_id,
        )
        indexer = DocumentIndexer(drive_client, es, settings.es_index)
        summary = indexer.sync()
        return {"status": "ok", "summary": summary}
    except Exception as exc:
        LOGGER.exception("Sync failed")
        raise HTTPException(status_code=500, detail=str(exc))
