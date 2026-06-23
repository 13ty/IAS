#!/usr/bin/env python3
"""
capability_mapper.py — Kwatermistrz v2: Mapowanie repo_card na capability_map.

Czyta repo_card.json, dopasowuje do capability_taxonomy.json po słowach kluczowych,
zapisuje capability_map.json i aktualizuje timeline.json.

Użycie:
  python capability_mapper.py <repo_id>
  python capability_mapper.py <repo_id> --threshold 0.5
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from repo_utils import (
    ensure_repo_dir,
    load_repo_card,
    load_taxonomy,
    save_capability_map,
    save_timeline,
)

# --- Constants ---

VERSION = "1.0.0"


# --- Helpers ---


def _now() -> str:
    """Bieżący timestamp ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _build_corpus(card: dict) -> str:
    """Zbuduj przeszukiwalny korpus z repo_card (lowered)."""
    enriched = card.get("enriched") or {}
    context = card.get("context") or {}
    parts = [
        card.get("full_name", ""),
        enriched.get("description", ""),
        enriched.get("language", ""),
        context.get("ecosystem", ""),
        " ".join(enriched.get("topics", []) or []),
    ]
    return " ".join(parts).lower()


def _compute_confidence(coverage: float) -> str:
    """Określ poziom ufności na podstawie pokrycia."""
    if coverage >= 0.7:
        return "high"
    if coverage >= 0.4:
        return "medium"
    return "low"


def _load_or_create_timeline(repo_id: str) -> dict:
    """Wczytaj istniejący timeline lub stwórz nowy."""
    repo_dir = ensure_repo_dir(repo_id)
    path = os.path.join(repo_dir, "timeline.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data: dict = json.load(f)
            return data
    return {"repo_id": repo_id, "events": []}


# --- Core matching logic ---


def _score_all_capabilities(card: dict, taxonomy: dict) -> list[dict]:
    """Oceń wszystkie capability względem repo_card. Wyniki posortowane malejąco po coverage."""
    corpus = _build_corpus(card)
    results: list[dict] = []

    for domain in taxonomy.get("domains", []):
        domain_id = domain.get("id", "")
        for cap in domain.get("capabilities", []):
            cap_id = cap.get("id", "")
            cap_name = cap.get("name", "")
            keywords = cap.get("keywords") or []

            # Zbuduj listę terminów do sprawdzenia
            check_terms = [cap_name.lower(), cap_id.lower()]
            check_terms.extend(k.lower() for k in keywords)

            # Dopasuj terminy obecne w korpusie
            matched_terms = [t for t in check_terms if t in corpus]

            total = len(check_terms)
            matched = len(matched_terms)
            coverage = matched / total if total > 0 else 0.0

            results.append(
                {
                    "capability_id": cap_id,
                    "domain": domain_id,
                    "coverage": round(coverage, 2),
                    "matched_terms": matched_terms,
                    "confidence": _compute_confidence(coverage),
                }
            )

    results.sort(key=lambda x: x["coverage"], reverse=True)
    return results


# --- Główna logika ---


def map_repo(repo_id: str, threshold: float = 0.3) -> dict | None:
    """Wykonaj mapowanie capability dla repozytorium. Zwraca capability_map lub None."""
    # --- Wczytaj repo_card ---
    card = load_repo_card(repo_id)
    if not card:
        print(f"❌ Repo card not found: state/repos/{repo_id}/repo_card.json")
        return None

    full_name = card.get("full_name", repo_id)
    print(f"📋 Loaded repo_card for {full_name}")

    # --- Wczytaj taksonomię ---
    taxonomy = load_taxonomy()
    if not taxonomy:
        print("❌ capability_taxonomy.json not found")
        return None

    domains = taxonomy.get("domains", [])
    print(f"📋 Loaded taxonomy ({len(domains)} domains)")

    # --- Oceń wszystkie capability ---
    scored = _score_all_capabilities(card, taxonomy)

    # Filtruj po progu
    matched = [c for c in scored if c["coverage"] >= threshold]

    # --- Fallback: brak dopasowań powyżej progu ---
    if not matched:
        if scored:
            matched = [scored[0]]
            print(
                f"⚠️  No capabilities met threshold ({threshold}), "
                f"including best match: {scored[0]['capability_id']} "
                f"(coverage={scored[0]['coverage']})"
            )
        else:
            print("⚠️  No capabilities matched at all (empty taxonomy?)")

    # --- Zbuduj podsumowanie ---
    domains_covered = sorted({c["domain"] for c in matched})
    dist: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for c in matched:
        dist[c["confidence"]] += 1

    # --- Zbuduj capability_map ---
    cap_map = {
        "version": VERSION,
        "repo_id": repo_id,
        "generated_at": _now(),
        "capabilities": matched,
        "summary": {
            "total_matched": len(matched),
            "domains_covered": domains_covered,
            "coverage_distribution": dist,
        },
    }

    # --- Zapisz capability_map ---
    map_path = save_capability_map(cap_map)
    print(f"💾 Saved capability map: {map_path}")

    # --- Zaktualizuj timeline ---
    timeline = _load_or_create_timeline(repo_id)
    timeline.setdefault("events", []).append(
        {
            "timestamp": _now(),
            "event": "capability_mapped",
            "data": {
                "total_matched": len(matched),
                "domains_covered": domains_covered,
            },
        }
    )
    tl_path = save_timeline(timeline)
    print(f"💾 Updated timeline: {tl_path}")

    # --- Podsumowanie na stdout ---
    print(f"✅ Capability mapping complete: {len(matched)} capabilities matched")
    print(f"   Domains covered: {', '.join(domains_covered)}")
    print(
        f"   Distribution: high={dist['high']}, medium={dist['medium']}, "
        f"low={dist['low']}"
    )

    return cap_map


# --- CLI entry point ---


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map repo_card.json → capability_map.json using capability_taxonomy.json"
    )
    parser.add_argument(
        "repo_id",
        help="UUID of the repo (directory in state/repos/)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Minimum coverage score to include a capability (default: 0.3)",
    )
    args = parser.parse_args()

    if args.threshold < 0.0 or args.threshold > 1.0:
        print("❌ --threshold must be between 0.0 and 1.0")
        sys.exit(1)

    result = map_repo(args.repo_id, args.threshold)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
