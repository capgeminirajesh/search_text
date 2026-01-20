"""Search service backed by Elasticsearch."""

from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch


class SearchService:
    def __init__(self, es: Elasticsearch, index_name: str) -> None:
        self._es = es
        self._index_name = index_name

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        response = self._es.search(
            index=self._index_name,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content", "name"],
                    }
                }
            },
            size=limit,
        )
        results = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            results.append(
                {
                    "name": source.get("name"),
                    "web_view_link": source.get("web_view_link"),
                }
            )
        return results
