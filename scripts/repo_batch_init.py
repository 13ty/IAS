#!/usr/bin/env python3
"""
repo_batch_init.py — Kwatermistrz: Inicjalizacja wsadowa folderów oceny repozytoriów.

Czyta N oczekujących wpisów z state/repo_queue.json, tworzy katalogi
state/repos/{repo_id}/ z minimalnym repo_card.json i timeline.json,
oznacza wpisy jako "initialized".

Użycie:
  python scripts/repo_batch_init.py              # Inicjalizuj 5 (domyślnie)
  python scripts/repo_batch_init.py 10           # Inicjalizuj 10
  python scripts/repo_batch_init.py --all        # Inicjalizuj wszystkie pending
  python scripts/repo_batch_init.py --dry-run    # Symulacja bez zapisu
"""

import argparse
import sys
from datetime import datetime, timezone

from repo_utils import (
    ensure_repo_dir,
    load_queue,
    parse_github_url,
    save_queue,
    save_repo_card,
    save_timeline,
)


# ── Budowa karty i timeline ────────────────────────────────────────────────


def _build_repo_card(item: dict, now_iso: str) -> dict:
    """Buduje minimalny repo_card dla wpisu z kolejki."""
    url = item["url"]
    parsed = parse_github_url(url)
    full_name = f"{parsed[0]}/{parsed[1]}" if parsed else url
    notes = item.get("notes", "")

    return {
        "id": item["id"],
        "url": url,
        "full_name": full_name,
        "context": {
            "ecosystem": "unknown",
            "category": "tool",
            "relationship_to_stack": "unknown",
            "discovery_trigger": item.get("gap_category", notes or "pending"),
        },
        "enriched": {
            "stars": 0,
            "description": notes,
            "language": "Unknown",
        },
        "analysis": {},
        "scoring": {
            "differentiation": 0,
            "capability_fit": 0,
            "integration_friction": 0,
            "community_vitality": 0,
            "code_quality": 0,
            "adoption_effort": 0,
            "overall_score": 0.0,
        },
        "decision": {
            "verdict": "PENDING",
            "decided_at": now_iso,
            "rationale": "Awaiting audit",
        },
        "tags": ["@repo"],
        "evaluated_at": now_iso,
    }


def _build_timeline(item: dict, now_iso: str) -> dict:
    """Buduje timeline z pojedynczym zdarzeniem 'queued'."""
    return {
        "version": "1.0.0",
        "repo_id": item["id"],
        "events": [
            {
                "timestamp": now_iso,
                "event": "queued",
                "data": {
                    "source": item.get("source", "unknown"),
                },
            }
        ],
    }


# ── Główna logika inicjalizacji ────────────────────────────────────────────


def init_items(items: list[dict], dry_run: bool = False) -> int:
    """Inicjalizuje foldery dla listy wpisów. Zwraca liczbę udanych."""
    now_iso = datetime.now(timezone.utc).isoformat()
    count = 0

    for item in items:
        repo_id = item["id"]
        url = item["url"]
        parsed = parse_github_url(url)
        full_name = f"{parsed[0]}/{parsed[1]}" if parsed else url

        print(f"  📦 [{repo_id[:8]}…] {full_name}")

        if dry_run:
            print(f"     → utworzyłby: state/repos/{repo_id}/repo_card.json")
            print(f"     → utworzyłby: state/repos/{repo_id}/timeline.json")
            print(f"     → zaktualizował: status → initialized")
            count += 1
            continue

        # --- Utwórz katalog ---
        ensure_repo_dir(repo_id)

        # --- Zapisz repo_card ---
        card = _build_repo_card(item, now_iso)
        card_path = save_repo_card(card)
        print(f"     ✅ repo_card: {card_path}")

        # --- Zapisz timeline ---
        timeline = _build_timeline(item, now_iso)
        timeline_path = save_timeline(timeline)
        print(f"     ✅ timeline: {timeline_path}")

        # --- Zaktualizuj status w kolejce ---
        item["status"] = "initialized"

        count += 1

    return count


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="repo_batch_init — inicjalizuj foldery oceny dla wpisów z kolejki",
    )
    parser.add_argument(
        "count",
        nargs="?",
        type=int,
        default=5,
        help="Liczba pending wpisów do inicjalizacji (domyślnie: 5)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inicjalizuj WSZYSTKIE pending wpisy (ignoruje count)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Symulacja — pokaż co zostanie zrobione bez zapisu",
    )
    args = parser.parse_args()

    # --- Wczytaj kolejkę ---
    queue = load_queue()
    items = queue.get("items", [])

    if not items:
        print("📭 Kolejka pusta. Dodaj wpisy przez /ias-audit lub add_to_queue().")
        sys.exit(0)

    # --- Filtruj pending ---
    pending = [item for item in items if item.get("status") == "pending"]

    if not pending:
        print("ℹ️  Brak oczekujących (pending) wpisów w kolejce.")
        remaining = sum(1 for i in items if i.get("status") != "decided")
        if remaining:
            print(f"   Pozostałe aktywne wpisy (non-decided): {remaining}")
        sys.exit(0)

    # --- Wybierz które inicjalizować ---
    to_init = pending if args.all else pending[: args.count]

    if args.all:
        print(f"\n🔧 Inicjalizuję WSZYSTKIE pending ({len(to_init)}/{len(pending)})…")
    else:
        print(
            f"\n🔧 Inicjalizuję {len(to_init)}/{len(pending)} pending wpisów "
            f"(użyj --all by inicjalizować wszystkie)…"
        )

    if args.dry_run:
        print(f"\n─── DRY RUN — nic nie zostanie zapisane ───\n")

    # --- Wykonaj ---
    done = init_items(to_init, dry_run=args.dry_run)

    # --- Zapisz zaktualizowaną kolejkę (tylko jeśli nie dry-run) ---
    if not args.dry_run and done > 0:
        save_queue(queue)

    # --- Podsumowanie ---
    mode = " (dry-run)" if args.dry_run else ""
    print(f"\n✅ Inicjalizacja zakończona{mode}: {done}/{len(to_init)}")
    remaining_pending = sum(1 for i in items if i.get("status") == "pending")
    if remaining_pending:
        print(f"⏳ Pozostało pending: {remaining_pending}")
    else:
        print(f"🎉 Wszystkie wpisy zainicjalizowane!")


if __name__ == "__main__":
    main()
