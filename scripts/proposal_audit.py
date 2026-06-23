#!/usr/bin/env python3
"""
proposal_audit.py — Kwatermistrz v2: Audyt repozytoriów z kolejki.

Ocenia repozytoria z state/repo_queue.json względem kryteriów ze scoring_criteria.json.
Zapisuje wyniki do state/repos/{repo_id}/repo_card.json i aktualizuje repo_knowledge.json.

Użycie:
  python proposal_audit.py                          # Audytuj wszystkie pending
  python proposal_audit.py --all                     # Audytuj wszystkie niezależnie od statusu
  python proposal_audit.py --id <uuid>               # Audytuj konkretny wpis po UUID
  python proposal_audit.py --non-interactive         # Automatyczne domyślne oceny (wszystkie 5)
  python proposal_audit.py --skip-analyze            # Pomiń analyzer_check.py
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Import z repo_utils
from repo_utils import (
    add_to_knowledge_index,
    compute_verdict,
    load_queue,
    load_scoring_criteria,
    normalize_github_url,
    parse_github_url,
    save_queue,
    save_repo_card,
    save_timeline,
)

# --- Ścieżki ---
IAS_ROOT = os.path.dirname(os.path.dirname(__file__))
SCRIPTS_DIR = Path(IAS_ROOT) / "scripts"
STATE_DIR = os.path.join(IAS_ROOT, "state")
REPOS_DIR = os.path.join(STATE_DIR, "repos")


# ── Analyzer ────────────────────────────────────────────────────────────────


def _run_analyzer(url: str, timeout: int = 120) -> dict | None:
    """Uruchom analyzer_check.py na URL GitHub, zwróć JSON lub None."""
    is_github = "github.com" in url
    if not is_github:
        return None

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    tmp_path = tmp.name
    tmp.close()

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "analyzer_check.py"),
                url,
                "--json",
                "--output",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"   ⚠️  analyzer_check.py exit code {result.returncode}")
            return None
        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  analyzer_check.py timeout ({timeout}s)")
        return None
    except json.JSONDecodeError as e:
        print(f"   ⚠️  analyzer_check.py JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"   ⚠️  analyzer_check.py error: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _compute_code_quality(analyzer_result: dict) -> float | None:
    """Przelicz wynik analyzer_check na score code_quality 1-10."""
    if not analyzer_result:
        return None
    ca = analyzer_result.get("clean_architecture", {})
    mi = analyzer_result.get("maintainability", {})

    ca_score = ca.get("score") if isinstance(ca.get("score"), (int, float)) else None
    mi_score = mi.get("index") if isinstance(mi.get("index"), (int, float)) else None

    scores = []
    if ca_score is not None:
        scores.append(ca_score / 10.0)  # 0-100 → 0-10
    if mi_score is not None:
        scores.append(mi_score / 10.0)  # 0-100 → 0-10

    if not scores:
        return None

    raw = sum(scores) / len(scores)
    return round(max(1, min(10, raw)), 1)


def _extract_analysis(analyzer_result: dict) -> dict:
    """Wyciągnij dane analysis z wyniku analyzer_check."""
    if not analyzer_result:
        return {}
    ca = analyzer_result.get("clean_architecture", {})
    mi = analyzer_result.get("maintainability", {})
    return {
        "clean_architecture_score": (
            ca.get("score") if isinstance(ca.get("score"), (int, float)) else None
        ),
        "maintainability_index": (
            mi.get("index") if isinstance(mi.get("index"), (int, float)) else None
        ),
        "loc": mi.get("loc"),
        "file_count": mi.get("fileCount"),
        "violations": ca.get("violations", []),
    }


# ── Interaktywne promptowanie ──────────────────────────────────────────────


def _prompt_score(label: str, description: str, weight: float, default: int = 5) -> int:
    """Poproś użytkownika o ocenę 1-10 z opisem i wagą."""
    print()
    print(f"   [{label}]")
    print(f"   Opis: {description}")
    print(f"   Waga: {weight:.0%}")
    while True:
        raw = input(f"   → {label} (1-10, Enter={default}): ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if 1 <= val <= 10:
                return val
        except ValueError:
            pass
        print(f"   ⚠️  Wprowadź liczbę od 1 do 10.")


def _prompt_context(queue_item: dict, non_interactive: bool) -> dict:
    """Zbierz dane kontekstowe dla repo_card."""
    if non_interactive:
        return {
            "ecosystem": "unknown",
            "category": "tool",
            "relationship_to_stack": "unknown",
            "discovery_trigger": queue_item.get(
                "gap_category", queue_item.get("notes", "manual")
            ),
        }

    print()
    print("   ── Kontekst ──")
    ecosystem = input(
        "   Ekosystem (np. testing, ci-cd, monitoring, Enter=unknown): "
    ).strip()
    if not ecosystem:
        ecosystem = "unknown"

    category = input(
        "   Typ (framework/library/tool/platform/language/application/template/other, Enter=tool): "
    ).strip()
    if not category:
        category = "tool"
    valid_categories = {
        "framework",
        "library",
        "tool",
        "platform",
        "language",
        "application",
        "template",
        "other",
    }
    if category not in valid_categories:
        print(f"   ⚠️  '{category}' nie jest standardową kategorią, używam 'other'")
        category = "other"

    relationship = input(
        "   Relacja do stacku (competitor/complement/replacement/novel/unknown, Enter=unknown): "
    ).strip()
    if not relationship:
        relationship = "unknown"
    valid_relations = {"competitor", "complement", "replacement", "novel", "unknown"}
    if relationship not in valid_relations:
        print(f"   ⚠️  '{relationship}' nie jest standardową relacją, używam 'unknown'")
        relationship = "unknown"

    trigger = input(
        f"   Discovery trigger (Enter={queue_item.get('gap_category', queue_item.get('notes', 'manual'))}): "
    ).strip()
    if not trigger:
        trigger = queue_item.get("gap_category", queue_item.get("notes", "manual"))

    return {
        "ecosystem": ecosystem,
        "category": category,
        "relationship_to_stack": relationship,
        "discovery_trigger": trigger,
    }


def _prompt_tags(
    non_interactive: bool, default_tags: list[str] | None = None
) -> list[str]:
    """Zbierz tagi dla repo_card."""
    if non_interactive:
        return default_tags or ["@repo"]

    raw = input(
        f"   Tagi (oddzielone spacją, Enter={', '.join(default_tags or ['@repo'])}): "
    ).strip()
    if not raw:
        return default_tags or ["@repo"]
    tags = []
    for t in raw.split():
        if not t.startswith("@"):
            t = f"@{t}"
        tags.append(t)
    return tags


def _prompt_rationale(non_interactive: bool, verdict: str) -> str:
    """Zbierz uzasadnienie decyzji."""
    if non_interactive:
        return f"Automatic audit — verdict: {verdict}"
    return (
        input("   Uzasadnienie (Enter=domyślne): ").strip()
        or f"Audit completed — verdict: {verdict}"
    )


# ── Scoring ────────────────────────────────────────────────────────────────


def _load_weights(scoring: dict | None) -> dict[str, float]:
    """Wyciągnij wagi z scoring_criteria.json."""
    weights = {
        "differentiation": 0.30,
        "capability_fit": 0.25,
        "integration_friction": 0.15,
        "community_vitality": 0.10,
        "code_quality": 0.10,
        "adoption_effort": 0.10,
    }
    if scoring and "dimensions" in scoring:
        for dim in scoring["dimensions"]:
            dim_id = dim.get("id")
            w = dim.get("weight")
            if dim_id and w is not None:
                weights[dim_id] = w
    return weights


def _compute_overall(scores: dict[str, int], weights: dict[str, float]) -> float:
    """Oblicz weighted overall score. Wszystkie score są 1-10, higher = better."""
    total = 0.0
    for dim, score in scores.items():
        w = weights.get(dim, 0)
        total += score * w
    return round(total, 2)


# ── Główna logika audytu ──────────────────────────────────────────────────


def _print_dim_table(scores: dict, weights: dict, overall: float, verdict: str) -> None:
    """Wydrukuj tabelę scoringową do stdout."""
    print(f"\n   ┌──────────────────────────────┬──────┬───────┬────────┐")
    print(f"   │ Wymiar                       │ Waga │ Score │ Ważony │")
    print(f"   ├──────────────────────────────┼──────┼───────┼────────┤")
    for dim, label in [
        ("differentiation", "Dyferencjacja"),
        ("capability_fit", "Dopasowanie capability"),
        ("integration_friction", "Tarcie integracyjne"),
        ("community_vitality", "Witalność społeczności"),
        ("code_quality", "Jakość kodu"),
        ("adoption_effort", "Koszt adopcji"),
    ]:
        s = scores.get(dim, 0)
        w = weights.get(dim, 0)
        weighted = s * w
        print(f"   │ {label:28s} │ {w:.0%} │ {s}/10   │ {weighted:.2f}  │")
    print(f"   ├──────────────────────────────┼──────┼───────┼────────┤")
    print(f"   │ OVERALL                      │      │       │ {overall:.2f}  │")
    print(f"   │ VERDICT                      │      │       │ {verdict:8s} │")
    print(f"   └──────────────────────────────┴──────┴───────┴────────┘")


def audit_item(
    queue_item: dict, non_interactive: bool = False, skip_analyze: bool = False
) -> dict | None:
    """Wykonaj pełny audyt pojedynczego wpisu z kolejki."""
    url = queue_item["url"]
    repo_id = queue_item["id"]
    notes = queue_item.get("notes", "")
    source = queue_item.get("source", "unknown")

    print(f"\n{'=' * 62}")
    print(f"  📋 Audyt: {url}")
    print(f"     ID: {repo_id}  |  Źródło: {source}  |  Notatki: {notes}")
    print(f"{'=' * 62}")

    # --- Parsuj URL ---
    parsed = parse_github_url(url)
    full_name = f"{parsed[0]}/{parsed[1]}" if parsed else url

    # --- Analyzer ---
    analyzer_result = None if skip_analyze else _run_analyzer(url)
    code_quality = _compute_code_quality(analyzer_result)
    analysis = _extract_analysis(analyzer_result)

    if analyzer_result:
        ca = analyzer_result.get("clean_architecture", {})
        mi = analyzer_result.get("maintainability", {})
        print(f"\n   📊 Analyzer Check — real data:")
        print(
            f"      Clean Architecture: {ca.get('score', 'N/A')}/100  ({ca.get('violationCount', '?')} naruszeń)"
        )
        print(
            f"      Maintainability:    {mi.get('index', 'N/A')}/100  ({mi.get('loc', '?')} LOC, {mi.get('fileCount', '?')} plików)"
        )
        if code_quality is not None:
            print(f"      Jakość kodu (przeliczona): {code_quality}/10")
    else:
        if skip_analyze:
            print(f"\n   ⏩ Pominięto analyzer (--skip-analyze)")
        else:
            print(f"\n   ⚠️  analyzer_check nie zwrócił danych")

    # --- Wczytaj scoring criteria z wagami ---
    scoring = load_scoring_criteria()
    weights = _load_weights(scoring)

    print(f"\n   ── Scoring Dimensions ──")

    # --- Promptuj każdy wymiar ---
    scores: dict[str, int] = {}

    if non_interactive:
        # Domyślne: wszystkie 5, code_quality z analyzer jeśli dostępny
        scores["differentiation"] = 5
        scores["capability_fit"] = 5
        scores["integration_friction"] = 5
        scores["community_vitality"] = 5
        scores["code_quality"] = int(code_quality) if code_quality is not None else 5
        scores["adoption_effort"] = 5
    else:
        # Znajdź opisy z scoring_criteria.json
        dim_descriptions = {}
        if scoring and "dimensions" in scoring:
            for dim in scoring["dimensions"]:
                dim_descriptions[dim["id"]] = dim.get("description", "")

        scores["differentiation"] = _prompt_score(
            "differentiation",
            dim_descriptions.get("differentiation", "Jak unikatowe jest to repo?"),
            weights.get("differentiation", 0.30),
            default=5,
        )
        scores["capability_fit"] = _prompt_score(
            "capability_fit",
            dim_descriptions.get(
                "capability_fit", "Jak dobrze pokrywa nasze potrzeby?"
            ),
            weights.get("capability_fit", 0.25),
            default=5,
        )
        scores["integration_friction"] = _prompt_score(
            "integration_friction",
            dim_descriptions.get(
                "integration_friction",
                "Jak łatwo wpiąć w nasz stack? Wyższy = mniejsze tarcie.",
            ),
            weights.get("integration_friction", 0.15),
            default=5,
        )
        scores["community_vitality"] = _prompt_score(
            "community_vitality",
            dim_descriptions.get(
                "community_vitality",
                "Czy społeczność żyje? Release cycle, odpowiedzi na issue.",
            ),
            weights.get("community_vitality", 0.10),
            default=5,
        )

        # code_quality: pokaż sugestię z analyzer jeśli dostępna
        cq_default = int(code_quality) if code_quality is not None else 5
        cq_desc = dim_descriptions.get(
            "code_quality", "Clean Architecture + Maintainability Index."
        )
        if code_quality is not None:
            cq_desc += f" Sugerowane: {code_quality}/10 (z analyzer_check)"
        scores["code_quality"] = _prompt_score(
            "code_quality",
            cq_desc,
            weights.get("code_quality", 0.10),
            default=cq_default,
        )

        scores["adoption_effort"] = _prompt_score(
            "adoption_effort",
            dim_descriptions.get(
                "adoption_effort", "Ile kosztuje wdrożenie? Wyższy = niższy koszt."
            ),
            weights.get("adoption_effort", 0.10),
            default=5,
        )

    # --- Oblicz overall ---
    overall = _compute_overall(scores, weights)

    # --- Określ verdict ---
    verdict = compute_verdict(overall)

    # --- Wydrukuj tabelę ---
    _print_dim_table(scores, weights, overall, verdict)

    # --- Zbierz kontekst ---
    context = _prompt_context(queue_item, non_interactive)

    # --- Zbierz tagi ---
    lang_tag = ""
    if analysis.get("file_count"):
        # Nie mamy pewnego języka z analyzer_check, pomiń
        pass
    default_tags = ["@repo"]
    if source != "unknown":
        default_tags.append(f"@{source}")
    tags = _prompt_tags(non_interactive, default_tags=default_tags)

    # --- Zbierz uzasadnienie ---
    rationale = _prompt_rationale(non_interactive, verdict)

    # --- Zbuduj repo_card ---
    now_iso = datetime.now(timezone.utc).isoformat()
    card = {
        "id": repo_id,
        "url": url,
        "full_name": full_name,
        "context": context,
        "enriched": {
            "stars": 0,
            "description": notes or "",
            "language": "Unknown",
            "license": "Unknown",
            "topics": [],
            "last_updated": now_iso,
        },
        "analysis": analysis,
        "scoring": {
            "differentiation": scores["differentiation"],
            "capability_fit": scores["capability_fit"],
            "integration_friction": scores["integration_friction"],
            "community_vitality": scores["community_vitality"],
            "code_quality": scores["code_quality"],
            "adoption_effort": scores["adoption_effort"],
            "overall_score": overall,
        },
        "decision": {
            "verdict": verdict,
            "decided_at": now_iso,
            "rationale": rationale,
        },
        "tags": tags,
        "evaluated_at": now_iso,
    }

    # --- Zapisz repo_card ---
    card_path = save_repo_card(card)
    print(f"\n   💾 Zapisano repo_card: {card_path}")

    # --- Zapisz timeline ---
    timeline = {
        "repo_id": repo_id,
        "events": [
            {
                "timestamp": now_iso,
                "event": "audited",
                "data": {
                    "verdict": verdict,
                    "overall_score": overall,
                    "scores": scores,
                },
            }
        ],
    }
    timeline_path = save_timeline(timeline)
    print(f"   💾 Zapisano timeline: {timeline_path}")

    # --- Dodaj do knowledge index ---
    repo_entry = {
        "id": repo_id,
        "url": url,
        "full_name": full_name,
        "verdict": verdict,
        "overall_score": overall,
        "ecosystem": context.get("ecosystem", "unknown"),
        "language": "Unknown",
        "tags": tags,
        "evaluated_at": now_iso,
    }
    add_to_knowledge_index(repo_entry)
    print(f"   💾 Zaktualizowano repo_knowledge.json")

    # --- Optional: vault_writer ---
    try:
        from vault_writer import write_repo_analysis

        vs = scores
        ae_score = scores.get("adoption_effort", 5)

        vault_data = {
            "repo_full_name": full_name,
            "repo_url": url,
            "primary_language": "Unknown",
            "stars": 0,
            "license": "Unknown",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "mission": f"Propozycja: {full_name}",
            "personality": notes or "W toku",
            "feature_matrix": [],
            "unique_points": [],
            "not_what": "",
            "strengths": [],
            "challenges": [],
            "inspiration": "",
            "adoption_effort": {
                "czas_nauki": ae_score,
                "migracja": ae_score,
                "testy": ae_score,
                "wsparcie": ae_score,
            },
            "value_score": {
                "nowe_funkcje": vs.get("differentiation", 5),
                "jakosc_vs_nasze": vs.get("code_quality", 5),
                "integracje": vs.get("integration_friction", 5),
                "wydajnosc": vs.get("capability_fit", 5),
            },
            "net_benefit": overall,
            "verdict": verdict,
            "team_acceptance": {
                "kto_uzywa": "Wszyscy agenci",
                "radość_frustracja": "radość",
                "sprzeciw": "brak",
                "ryzyko_buntu": 2,
            },
            "learning_value": {
                "wzorzec": "",
                "inspiracja": "",
                "anti_wzorzec": "",
                "architektura": "",
            },
            "notes": notes,
            "justification": rationale,
        }
        vault_path = write_repo_analysis(vault_data)
        print(f"   📝 Zapisano do vault: {vault_path}")
    except ImportError:
        pass
    except Exception as e:
        print(f"   ⚠️  vault_writer error (non-fatal): {e}")

    return card


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    # --- Parsuj argumenty ---
    all_flag = "--all" in sys.argv
    id_filter = None
    if "--id" in sys.argv:
        idx = sys.argv.index("--id")
        if len(sys.argv) > idx + 1:
            id_filter = sys.argv[idx + 1]
    non_interactive = "--non-interactive" in sys.argv
    skip_analyze = "--skip-analyze" in sys.argv

    # --- Wczytaj kolejkę ---
    queue = load_queue()
    items = queue.get("items", [])

    if not items:
        print("📭 Kolejka pusta. Dodaj wpisy przez /ias-audit lub add_to_queue().")
        sys.exit(0)

    # --- Filtruj ---
    to_audit: list[dict] = []
    for item in items:
        if id_filter is not None:
            if item["id"] == id_filter:
                to_audit.append(item)
            continue
        if all_flag or item.get("status") == "pending":
            to_audit.append(item)

    if not to_audit:
        print("ℹ️  Brak wpisów do audytu.")
        if id_filter:
            print(f"   Nie znaleziono wpisu o ID: {id_filter}")
        else:
            print("   Użyj --all by przeaudytować wszystkie, lub --id <uuid>.")
        sys.exit(0)

    # --- Audytuj ---
    print(f"\n🔍 Rozpoczynam audyt {len(to_audit)} repozytoriów...\n")

    results: list[tuple[str, dict]] = []
    for item in to_audit:
        card = audit_item(
            item, non_interactive=non_interactive, skip_analyze=skip_analyze
        )
        if card:
            results.append((item["id"], card))

            # --- Zaktualizuj status w kolejce ---
            for q_item in queue["items"]:
                if q_item["id"] == item["id"]:
                    q_item["status"] = "decided"
                    q_item["decided_at"] = datetime.now(timezone.utc).isoformat()
                    break

            save_queue(queue)

    # --- Podsumowanie ---
    print(f"\n{'=' * 62}")
    print(f"  📊 PODSUMOWANIE AUDYTU")
    print(f"{'=' * 62}")
    print(f"\n  Audytowane: {len(results)}/{len(items)}")
    for rid, card in results:
        v = card["decision"]["verdict"]
        s = card["scoring"]["overall_score"]
        print(f"    [{rid[:8]}…] {card['full_name']} → {v} ({s})")

    remaining = sum(1 for i in items if i.get("status") == "pending")
    if remaining:
        print(f"\n  ⏳ Pozostało do audytu: {remaining}")
    else:
        print(f"\n  ✅ Wszystkie wpisy zaudytowane!")


if __name__ == "__main__":
    main()
