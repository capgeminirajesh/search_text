"""Google Drive client for listing and downloading files."""

from __future__ import annotations

import io
import logging
from typing import Iterable

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.models import StorageFile


LOGGER = logging.getLogger(__name__)


class GoogleDriveClient:
    def __init__(self, credentials_path: str, folder_id: str | None = None) -> None:
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=scopes,
        )
        self._service = build("drive", "v3", credentials=credentials)
        self._folder_id = folder_id

    def list_files(self) -> list[StorageFile]:
        query_parts = ["trashed=false"]
        if self._folder_id:
            query_parts.append(f"'{self._folder_id}' in parents")
        query = " and ".join(query_parts)
        LOGGER.info("Drive list query: %s", query)

        files: list[StorageFile] = []
        page_token = None
        while True:
            response = (
                self._service.files()
                .list(
                    q=query,
                    corpora="allDrives",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)",
                    includeItemsFromAllDrives=True,
                    pageToken=page_token,
                    supportsAllDrives=True,
                )
                .execute()
            )
            for item in response.get("files", []):
                LOGGER.info("Drive file: %s (%s)", item.get("name"), item.get("id"))
                files.append(
                    StorageFile(
                        file_id=item["id"],
                        name=item.get("name", ""),
                        mime_type=item.get("mimeType", ""),
                        modified_time=item.get("modifiedTime"),
                        size=int(item["size"]) if "size" in item else None,
                        web_view_link=item.get("webViewLink"),
                    )
                )
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        LOGGER.info("Drive files fetched: %s", len(files))
        return files

    def download_file(self, drive_file: StorageFile) -> bytes:
        if drive_file.mime_type.startswith("application/vnd.google-apps"):
            return self._export_google_doc(drive_file.file_id)
        return self._download_binary(drive_file.file_id)

    def _export_google_doc(self, file_id: str) -> bytes:
        request = self._service.files().export_media(fileId=file_id, mimeType="text/plain")
        return self._consume_download(request)

    def _download_binary(self, file_id: str) -> bytes:
        request = self._service.files().get_media(fileId=file_id)
        return self._consume_download(request)

    @staticmethod
    def _consume_download(request) -> bytes:
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                LOGGER.debug("Download progress: %s", int(status.progress() * 100))
        return fh.getvalue()
