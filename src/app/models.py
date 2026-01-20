"""Data models for search indexing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StorageFile:
    file_id: str
    name: str
    mime_type: str
    modified_time: str | None
    size: int | None
    web_view_link: str | None


@dataclass(frozen=True)
class IndexedDocument:
    file_id: str
    name: str
    mime_type: str
    modified_time: str | None
    size: int | None
    web_view_link: str | None
    content: str
