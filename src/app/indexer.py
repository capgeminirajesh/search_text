"""Index Google Drive files into Elasticsearch."""

from __future__ import annotations

import io
import logging
from typing import Iterable

from elasticsearch import Elasticsearch
from elasticsearch import helpers

from app.google_drive_client import GoogleDriveClient
from app.models import IndexedDocument, StorageFile


LOGGER = logging.getLogger(__name__)


class DocumentIndexer:
    def __init__(self, drive_client: GoogleDriveClient, es: Elasticsearch, index_name: str) -> None:
        self._drive_client = drive_client
        self._es = es
        self._index_name = index_name

    def ensure_index(self) -> None:
        if self._es.indices.exists(index=self._index_name):
            return
        mapping = {
            "mappings": {
                "properties": {
                    "file_id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "mime_type": {"type": "keyword"},
                    "modified_time": {"type": "date"},
                    "size": {"type": "long"},
                    "web_view_link": {"type": "keyword"},
                    "content": {"type": "text"},
                }
            }
        }
        self._es.indices.create(index=self._index_name, body=mapping)
        LOGGER.info("Created Elasticsearch index: %s", self._index_name)

    def sync(self) -> dict[str, int]:
        self.ensure_index()
        drive_files = self._drive_client.list_files()
        indexed_docs = [self._build_document(df) for df in drive_files]

        actions = (
            {
                "_index": self._index_name,
                "_id": doc.file_id,
                "_source": {
                    "file_id": doc.file_id,
                    "name": doc.name,
                    "mime_type": doc.mime_type,
                    "modified_time": doc.modified_time,
                    "size": doc.size,
                    "web_view_link": doc.web_view_link,
                    "content": doc.content,
                },
            }
            for doc in indexed_docs
        )

        success, _ = helpers.bulk(self._es, actions, refresh=True)
        LOGGER.info("Indexed documents: %s", success)

        deleted = self._delete_stale_documents({doc.file_id for doc in indexed_docs})
        return {"indexed": success, "deleted": deleted}

    def _build_document(self, storage_file: StorageFile) -> IndexedDocument:
        raw_content = self._drive_client.download_file(storage_file)
        text = self._extract_text(storage_file, raw_content)
        return IndexedDocument(
            file_id=storage_file.file_id,
            name=storage_file.name,
            mime_type=storage_file.mime_type,
            modified_time=storage_file.modified_time,
            size=storage_file.size,
            web_view_link=storage_file.web_view_link,
            content=text,
        )

    def _delete_stale_documents(self, live_ids: set[str]) -> int:
        stale_ids = []
        response = self._es.search(
            index=self._index_name,
            body={"_source": ["file_id"], "query": {"match_all": {}}},
            size=10000,
        )
        for hit in response.get("hits", {}).get("hits", []):
            file_id = hit.get("_source", {}).get("file_id")
            if file_id and file_id not in live_ids:
                stale_ids.append(hit.get("_id"))

        deleted = 0
        for doc_id in stale_ids:
            self._es.delete(index=self._index_name, id=doc_id)
            deleted += 1
        if deleted:
            self._es.indices.refresh(index=self._index_name)
        LOGGER.info("Deleted stale documents: %s", deleted)
        return deleted

    def _extract_text(self, storage_file: StorageFile, content: bytes) -> str:
        mime = storage_file.mime_type
        if mime in {"text/plain", "text/csv"} or mime.startswith("application/vnd.google-apps"):
            return content.decode("utf-8", errors="ignore")
        if mime == "application/pdf":
            return self._extract_pdf(content)
        if mime in {"image/png", "image/jpeg"}:
            return self._extract_image(content)

        # Default fallback: attempt UTF-8 decode.
        return content.decode("utf-8", errors="ignore")

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            LOGGER.warning("pdfminer.six not installed; skipping PDF text extraction")
            return ""
        with io.BytesIO(content) as handle:
            return extract_text(handle) or ""

    @staticmethod
    def _extract_image(content: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            LOGGER.warning("pytesseract/Pillow not installed; skipping image OCR")
            return ""
        with io.BytesIO(content) as handle:
            image = Image.open(handle)
            return pytesseract.image_to_string(image) or ""
