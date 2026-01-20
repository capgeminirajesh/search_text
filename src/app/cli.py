"""Simple CLI client for the search API."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


DEFAULT_API = "http://127.0.0.1:8000"


def _print_results(results: list[dict[str, Any]]) -> None:
    if not results:
        print("No matches")
        return
    for item in results:
        name = item.get("name")
        link = item.get("web_view_link")
        score = item.get("score")
        print(f"{name} | {link} | score={score}")


def cmd_search(args: argparse.Namespace) -> int:
    response = requests.get(f"{args.api_url}/search", params={"q": args.query, "limit": args.limit})
    response.raise_for_status()
    payload = response.json()
    _print_results(payload.get("results", []))
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    response = requests.post(f"{args.api_url}/sync")
    response.raise_for_status()
    payload = response.json()
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Drive search CLI")
    parser.add_argument("--api-url", default=DEFAULT_API)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search for text")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.set_defaults(func=cmd_search)

    sync_parser = subparsers.add_parser("sync", help="Sync index from Drive")
    sync_parser.set_defaults(func=cmd_sync)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())