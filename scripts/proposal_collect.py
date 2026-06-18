#!/usr/bin/env python3
"""
proposal_collect.py — Kwatermistrz: Zbieranie propozycji narzędzi.

Dodaje URL-e do data/proposals.csv z automatyczną detekcją typu.
Użycie:
  python proposal_collect.py https://github.com/user/repo "notatki"
  python proposal_collect.py --list
  python proposal_collect.py --status pending
"""

import csv
import os
import sys
from datetime import datetime, timezone

PROPOSALS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "proposals.csv"
)
HEADERS = ["timestamp", "url", "source", "type", "notes", "status"]


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


def load_proposals() -> list[dict]:
    """Wczytaj wszystkie propozycje z CSV."""
    if not os.path.exists(PROPOSALS_PATH):
        return []
    with open(PROPOSALS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def save_proposals(proposals: list[dict]) -> None:
    """Zapisz propozycje do CSV."""
    with open(PROPOSALS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in proposals:
            writer.writerow(row)


def add_proposal(url: str, notes: str = "", source: str = "user") -> dict:
    """Dodaj pojedynczą propozycję."""
    proposals = load_proposals()

    # Sprawdź duplikaty
    existing_urls = {p["url"].strip().rstrip("/") for p in proposals}
    clean_url = url.strip().rstrip("/")
    if clean_url in existing_urls:
        print(f"⚠️  URL już istnieje w proposals.csv: {url}")
        return {"status": "duplicate"}

    proposal = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "url": clean_url,
        "source": source,
        "type": detect_type(url),
        "notes": notes,
        "status": "pending",
    }
    proposals.append(proposal)
    save_proposals(proposals)
    print(f"✅ Dodano propozycję: {url} ({proposal['type']})")
    return proposal


def list_proposals(status: str | None = None) -> None:
    """Wyświetl wszystkie propozycje, opcjonalnie filtrując po statusie."""
    proposals = load_proposals()
    if not proposals:
        print("📭 Brak propozycji w proposals.csv")
        return

    filtered = [p for p in proposals if status is None or p["status"] == status]

    print(f"\n📋 Propozycje ({len(filtered)}/{len(proposals)}):\n")
    print(f"{'STATUS':<12} {'TYP':<18} {'URL'}")
    print("-" * 80)
    for p in filtered:
        print(f"{p['status']:<12} {p['type']:<18} {p['url']}")
    print()

    # Podsumowanie
    statuses = {}
    for p in proposals:
        statuses[p["status"]] = statuses.get(p["status"], 0) + 1
    print("Podsumowanie:", ", ".join(f"{k}: {v}" for k, v in statuses.items()))


def main():
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python proposal_collect.py <url> [notatki]     — Dodaj propozycję")
        print("  python proposal_collect.py --list              — Lista wszystkich")
        print("  python proposal_collect.py --status pending    — Filtruj po statusie")
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_proposals()
    elif sys.argv[1] == "--status" and len(sys.argv) > 2:
        list_proposals(sys.argv[2])
    else:
        url = sys.argv[1]
        notes = sys.argv[2] if len(sys.argv) > 2 else ""
        add_proposal(url, notes)


if __name__ == "__main__":
    main()
