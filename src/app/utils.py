"""Shared helpers."""

from __future__ import annotations

from elasticsearch import Elasticsearch


def build_es_client(
    es_url: str,
    es_user: str | None,
    es_password: str | None,
    verify_certs: bool,
    ca_certs: str | None,
) -> Elasticsearch:
    if es_user and es_password:
        return Elasticsearch(
            es_url,
            basic_auth=(es_user, es_password),
            verify_certs=verify_certs,
            ca_certs=ca_certs,
        )
    return Elasticsearch(es_url, verify_certs=verify_certs, ca_certs=ca_certs)
