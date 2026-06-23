#!/usr/bin/env python3
"""
timeline_manager.py — Kwatermistrz: Zarządzanie timeline'em repozytoriów.

CLI to add, list, and show stats for timeline events on repos.

Użycie:
  python timeline_manager.py add <repo_id> --event <type> --data <json-string>
  python timeline_manager.py list <repo_id> [--limit N]
  python timeline_manager.py stats <repo_id>
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

from repo_utils import _now, load_repo_card, save_timeline

# --- Constants ---

REPO_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


# --- Helper functions ---


def _resolve_timeline_path(repo_id: str) -> str:
    """Zwraca ścieżkę do timeline.json dla danego repo_id."""
    from repo_utils import REPOS_DIR

    return os.path.join(REPOS_DIR, repo_id, "timeline.json")


def _load_timeline(repo_id: str) -> dict:
    """Wczytuje istniejący timeline lub zwraca nowy szkielet."""
    path = _resolve_timeline_path(repo_id)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"repo_id": repo_id, "events": []}


def _validate_repo_id(repo_id: str) -> bool:
    """Sprawdza czy repo_id ma poprawny format UUID."""
    if not REPO_ID_PATTERN.match(repo_id):
        print(f"❌ Invalid repo_id format: {repo_id}")
        print("   Expected UUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        return False
    return True


def _verify_repo_exists(repo_id: str) -> bool:
    """Sprawdza czy repo_card istnieje dla danego repo_id."""
    card = load_repo_card(repo_id)
    if card is None:
        print(f"❌ Repo not found: {repo_id}")
        return False
    return True


def _data_preview(data: dict, max_len: int = 80) -> str:
    """Zwraca skróconą reprezentację JSON data (do max_len znaków)."""
    raw = json.dumps(data, ensure_ascii=False)
    if len(raw) > max_len:
        return raw[: max_len - 3] + "..."
    return raw


# --- Section: Add command ---


def cmd_add(args: argparse.Namespace) -> None:
    """Dodaje event do timeline repozytorium."""
    repo_id = args.repo_id
    event_type = args.event.strip()
    message = (args.message or "").strip()

    # Walidacje
    if not _validate_repo_id(repo_id):
        sys.exit(1)
    if not _verify_repo_exists(repo_id):
        sys.exit(1)
    if not event_type:
        print("❌ --event cannot be empty")
        sys.exit(1)

    # Parsuj JSON data
    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in --data: {e}")
        sys.exit(1)
    if not isinstance(data, dict):
        print("❌ --data must be a JSON object (key-value pairs)")
        sys.exit(1)

    # Wczytaj lub utwórz timeline
    timeline = _load_timeline(repo_id)

    # Zbuduj event
    event: dict = {
        "timestamp": _now(),
        "event": event_type,
        "data": data,
    }
    if message:
        event["message"] = message

    timeline.setdefault("events", []).append(event)

    # Zapisz
    path = save_timeline(timeline)
    print(f"✅ Event added: {event_type}")
    print(f"   Timestamp: {event['timestamp']}")
    print(f"   Path: {path}")


# --- Section: List command ---


def cmd_list(args: argparse.Namespace) -> None:
    """Wyświetla eventy timeline w odwrotnej chronologii."""
    repo_id = args.repo_id

    if not _validate_repo_id(repo_id):
        sys.exit(1)
    if not _verify_repo_exists(repo_id):
        sys.exit(1)

    timeline = _load_timeline(repo_id)
    events = timeline.get("events", [])

    if not events:
        print(f"📋 No events for {repo_id}")
        return

    # Sortuj malejąco po timestamp (najnowsze pierwsze)
    sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""), reverse=True)
    display = sorted_events[: args.limit]

    print(f"📋 Timeline for {repo_id} ({len(events)} total, showing {len(display)}):")
    print()
    for i, ev in enumerate(display, 1):
        ts = ev.get("timestamp", "?")
        et = ev.get("event", "?")
        data_str = _data_preview(ev.get("data", {}))
        print(f"  {i}. [{ts}] {et}")
        print(f"     Data: {data_str}")


# --- Section: Stats command ---


def cmd_stats(args: argparse.Namespace) -> None:
    """Wyświetla statystyki timeline dla repozytorium."""
    repo_id = args.repo_id

    if not _validate_repo_id(repo_id):
        sys.exit(1)
    if not _verify_repo_exists(repo_id):
        sys.exit(1)

    timeline = _load_timeline(repo_id)
    events = timeline.get("events", [])

    if not events:
        print(f"📊 No events for {repo_id}")
        return

    # Podstawowe statystyki
    total = len(events)
    timestamps = [e.get("timestamp", "") for e in events if e.get("timestamp")]
    first_ts = min(timestamps) if timestamps else "N/A"
    last_ts = max(timestamps) if timestamps else "N/A"

    # Grupowanie po typie eventu
    type_counts: Counter = Counter(e.get("event", "unknown") for e in events)

    print(f"📊 Timeline stats for {repo_id}:")
    print(f"   Total events:  {total}")
    print(f"   📅 First event: {first_ts}")
    print(f"   📅 Last event:  {last_ts}")
    print()
    print("   Events by type:")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 20)
        print(f"     {etype:<22s} {count:3d}  {bar}")


# --- Section: Main entry point ---


def main() -> None:
    """Główna funkcja CLI z subkomendami."""
    parser = argparse.ArgumentParser(
        description="Timeline Manager — zarządzanie timeline'em repozytoriów"
    )
    subparsers = parser.add_subparsers(dest="command", help="Dostępne komendy")

    # add
    ap_add = subparsers.add_parser("add", help="Dodaj event do timeline")
    ap_add.add_argument("repo_id", help="ID repozytorium (UUID)")
    ap_add.add_argument(
        "--event", required=True, help="Typ eventu (np. re-audited, note_added)"
    )
    ap_add.add_argument("--data", required=True, help="Dane eventu jako JSON string")
    ap_add.add_argument("--message", help="Opcjonalny opis wydarzenia")

    # list
    ap_list = subparsers.add_parser("list", help="Wyświetl eventy timeline")
    ap_list.add_argument("repo_id", help="ID repozytorium (UUID)")
    ap_list.add_argument(
        "--limit", type=int, default=20, help="Max liczba eventów (domyślnie: 20)"
    )

    # stats
    ap_stats = subparsers.add_parser("stats", help="Statystyki timeline")
    ap_stats.add_argument("repo_id", help="ID repozytorium (UUID)")

    args = parser.parse_args()

    # Routing subkomend
    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
