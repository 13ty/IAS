#!/usr/bin/env python3
"""
proposal_collect.py — Kwatermistrz v2: Zbieranie propozycji narzędzi.

Dodaje URL-e do state/repo_queue.json przez repo_utils.
Użycie:
  python proposal_collect.py https://github.com/user/repo "notatki"
  python proposal_collect.py https://github.com/user/repo --source scout --priority high
  python proposal_collect.py --list
  python proposal_collect.py --status pending
  python proposal_collect.py --stats
"""

import argparse
import sys

from repo_utils import (
    add_to_queue,
    list_queue,
    queue_stats,
    normalize_github_url,
)


# --- Typowanie URL-i (heurystyka, przydatne przy wyświetlaniu) ---


def detect_type(url: str) -> str:
    """Prosta heurystyka typu na podstawie URL."""
    url_lower = url.lower()
    if "github.com" in url_lower:
        return "repo"
    if "pypi.org" in url_lower or "pypi" in url_lower:
        return "python-package"
    if "npmjs.com" in url_lower or "npm" in url_lower:
        return "npm-package"
    if "docker" in url_lower:
        return "docker-image"
    if "marketplace" in url_lower or "vsmarketplace" in url_lower:
        return "vscode-extension"
    return "other"


# --- CLI ---


def cmd_add(
    url: str, source: str, priority: str, gap_category: str | None, notes: str
) -> None:
    """Dodaj URL do kolejki przez repo_utils."""
    result = add_to_queue(
        url=url,
        source=source,
        priority=priority,
        gap_category=gap_category,
        notes=notes,
    )
    if result:
        detected = detect_type(url)
        print(f"   Typ (heurystyka): {detected}")
        print(f"   ID: {result['id']}")


def cmd_list(status: str | None) -> None:
    """Wyświetl wszystkie wpisy w kolejce."""
    items = list_queue(status=status)
    if not items:
        print("📭 Kolejka pusta.")
        return

    total_all = len(list_queue())
    label = f" (filtr: {status})" if status else ""
    print(f"\n📋 Kolejka repozytoriów ({len(items)}/{total_all}){label}:\n")
    print(f"{'STATUS':<12} {'PRIO':<8} {'TYP':<18} {'URL'}")
    print("-" * 90)
    for item in items:
        detected = detect_type(item["url"])
        print(
            f"{item['status']:<12} {item['priority']:<8} {detected:<18} {item['url']}"
        )
    print()

    # Podsumowanie per status
    all_items = list_queue()
    statuses: dict[str, int] = {}
    for item in all_items:
        s = item["status"]
        statuses[s] = statuses.get(s, 0) + 1
    print("Podsumowanie:", ", ".join(f"{k}: {v}" for k, v in statuses.items()))


def cmd_stats() -> None:
    """Wyświetl statystyki kolejki."""
    stats = queue_stats()
    print(f"\n📊 Statystyki kolejki:\n")
    print(f"  Razem:     {stats.get('total', 0)}")
    for key in sorted(stats.keys()):
        if key == "total":
            continue
        print(f"  {key.capitalize():<10} {stats[key]}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Kwatermistrz — dodawanie propozycji narzędzi do kolejki.",
    )
    parser.add_argument("url", nargs="?", help="URL repozytorium GitHub")
    parser.add_argument("notes", nargs="?", default="", help="Opcjonalne notatki")
    parser.add_argument("--list", action="store_true", help="Wyświetl wszystkie wpisy")
    parser.add_argument(
        "--status",
        default=None,
        help="Filtruj po statusie (pending, in_progress, done)",
    )
    parser.add_argument("--stats", action="store_true", help="Statystyki kolejki")
    parser.add_argument(
        "--source", default="user", help="Źródło propozycji (domyślnie: user)"
    )
    parser.add_argument(
        "--priority",
        default="medium",
        choices=["low", "medium", "high", "critical"],
        help="Priorytet (domyślnie: medium)",
    )
    parser.add_argument(
        "--gap-category", default=None, help="Kategoria luki technologicznej"
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Flagi informacyjne
    if args.stats:
        cmd_stats()
        return

    if args.list or args.status:
        cmd_list(status=args.status)
        return

    # Dodawanie URL
    if not args.url:
        parser.print_help()
        sys.exit(1)

    cmd_add(
        url=args.url,
        source=args.source,
        priority=args.priority,
        gap_category=args.gap_category,
        notes=args.notes,
    )


if __name__ == "__main__":
    main()
