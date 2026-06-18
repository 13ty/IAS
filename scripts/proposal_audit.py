#!/usr/bin/env python3
"""
proposal_audit.py — Kwatermistrz: Audyt propozycji narzędzi.

Ocenia propozycje z data/proposals.csv względem gapów, nakładania i wartości.
Użycie:
  python proposal_audit.py                    # Audytuj wszystkie pending
  python proposal_audit.py --all              # Audytuj wszystkie
  python proposal_audit.py --id 0             # Audytuj konkretny wiersz
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

IAS_ROOT = os.path.dirname(os.path.dirname(__file__))
SCRIPTS_DIR = Path(IAS_ROOT) / "scripts"
PROPOSALS_PATH = os.path.join(IAS_ROOT, "data", "proposals.csv")
REGISTRY_PATH = os.path.join(IAS_ROOT, "data", "tool_registry.json")
AUDITS_DIR = os.path.join(IAS_ROOT, "data", "audits")
HEADERS = ["timestamp", "url", "source", "type", "notes", "status"]


def load_proposals() -> list[dict]:
    if not os.path.exists(PROPOSALS_PATH):
        return []
    with open(PROPOSALS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def save_proposals(proposals: list[dict]) -> None:
    with open(PROPOSALS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in proposals:
            writer.writerow(row)


def load_registry() -> dict:
    if not os.path.exists(REGISTRY_PATH):
        return {"tools": {}, "domains": {}}
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def slugify(url: str) -> str:
    """Stwórz nazwę pliku z URL."""
    name = url.rstrip("/").split("/")[-1] if "/" in url else url
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return f"{datetime.now().strftime('%Y%m%d')}_{name[:50]}"


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


def _compute_quality(analyzer_result: dict) -> float:
    """Przelicz wynik analyzer_check na score quality 1-10."""
    ca = analyzer_result.get("clean_architecture", {})
    mi = analyzer_result.get("maintainability", {})

    ca_score = ca.get("score", 0) / 10  # 0-100 → 0-10
    mi_score = mi.get("index", 0) / 10  # 0-100 → 0-10

    raw = (ca_score + mi_score) / 2 if (ca_score > 0 or mi_score > 0) else 6.0
    return round(max(1, min(10, raw)), 1)


def analyze_proposal(proposal: dict) -> dict:
    """Wykonaj audyt pojedynczej propozycji."""
    url = proposal["url"]
    notes = proposal.get("notes", "")

    print(f"\n{'=' * 60}")
    print(f"📋 Audyt: {url}")
    print(f"   Typ: {proposal['type']} | Notatki: {notes}")
    print(f"{'=' * 60}")

    # Krok 1: Ekstrakcja nazwy z URL
    repo_name = url.rstrip("/").split("/")[-2:] if "github.com" in url else [url]
    repo_full = "/".join(repo_name) if isinstance(repo_name, list) else url

    # Krok 2: Tool Registry - sprawdź nakładanie
    registry = load_registry()
    overlap_tools = []
    for tool_name, tool_data in registry.get("tools", {}).items():
        desc = tool_data.get("description", "").lower()
        domain = tool_data.get("domain", "").lower()
        if any(kw in desc for kw in notes.lower().split() if notes):
            overlap_tools.append(tool_name)

    has_overlap = len(overlap_tools) > 0

    # Krok 3: Decision Matrix z analyzer_check
    skip_analyze = "--skip-analyze" in sys.argv
    analyzer_result = None if skip_analyze else _run_analyzer(url)

    if analyzer_result:
        ca = analyzer_result.get("clean_architecture", {})
        mi = analyzer_result.get("maintainability", {})
        quality = _compute_quality(analyzer_result)
        print(f"\n   📊 Analyzer Check — real data:")
        print(
            f"      Clean Architecture: {ca.get('score', 'N/A')}/100  ({ca.get('violationCount', '?')} naruszeń)"
        )
        print(
            f"      Maintainability:    {mi.get('index', 'N/A')}/100  ({mi.get('loc', '?')} LOC, {mi.get('fileCount', '?')} plików)"
        )
        print(f"      Jakość (przeliczona): {quality}/10")
    else:
        if skip_analyze:
            print(f"\n   ⏩ Skipped analyzer (--skip-analyze)")
        else:
            print(f"\n   ⚠️  analyzer_check nie zwrócił danych — fallback do domyślnych")
        quality = 6.0

    gap_fit = 7
    team_fit = 5
    adoption_effort = 5

    if has_overlap:
        print(f"   ⚠️  Potencjalne nakładanie: {', '.join(overlap_tools)}")
        gap_fit = max(1, gap_fit - 3)
    else:
        print(f"   ✅ Brak nakładania z istniejącymi narzędziami")

    weights = {
        "gap_fit": 0.30,
        "quality": 0.25,
        "team_fit": 0.30,
        "adoption_effort": 0.15,
    }
    net_benefit = (
        gap_fit * weights["gap_fit"]
        + quality * weights["quality"]
        + team_fit * weights["team_fit"]
        + (10 - adoption_effort) * weights["adoption_effort"]
    )

    if net_benefit > 7.0:
        verdict = "ZAPROSZENIE DO TAŃCA 🎉"
    elif net_benefit > 4.0:
        verdict = "PILOT 🧪"
    else:
        verdict = "LEKCJA 📚"

    print(f"\n   📊 Decision Matrix:")
    print(f"      Gap Fit:         {gap_fit}/10 × 0.30 = {gap_fit * 0.30:.1f}")
    print(f"      Quality:         {quality}/10 × 0.25 = {quality * 0.25:.1f}")
    print(f"      Team Fit:        {team_fit}/10 × 0.30 = {team_fit * 0.30:.1f}")
    print(f"      Adoption Cost:   {adoption_effort}/10 (odwrócone)")
    print(f"      ─────────────────────────────────")
    print(f"      Net Benefit:     {net_benefit:.2f}/10")
    print(f"      Werdykt:         {verdict}")

    return {
        "proposal": proposal,
        "repo": repo_full,
        "overlap": {"has_overlap": has_overlap, "existing_tools": overlap_tools},
        "decision_matrix": {
            "gap_fit": gap_fit,
            "quality": quality,
            "team_fit": team_fit,
            "adoption_effort": adoption_effort,
            "net_benefit": round(net_benefit, 2),
            "verdict": verdict,
        },
    }


def save_audit(result: dict) -> str:
    """Zapisz wynik audytu do pliku .md."""
    os.makedirs(AUDITS_DIR, exist_ok=True)
    slug = slugify(result["proposal"]["url"])
    path = os.path.join(AUDITS_DIR, f"{slug}.md")

    dm = result["decision_matrix"]
    overlap = result["overlap"]

    content = f"""# Audyt Propozycji: {result["proposal"]["url"]}

**Data**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Typ**: {result["proposal"]["type"]}
**Status**: audited

## Decision Matrix

| Kryterium | Waga | Score |
|-----------|------|-------|
| Gap Fit | 0.30 | {dm["gap_fit"]}/10 |
| Quality | 0.25 | {dm["quality"]}/10 |
| Team Fit | 0.30 | {dm["team_fit"]}/10 |
| Adoption Effort | 0.15 | {dm["adoption_effort"]}/10 |

**Net Benefit**: {dm["net_benefit"]}/10
**Werdykt**: {dm["verdict"]}

## Overlap Detection

- **Nakładanie**: {"Tak" if overlap["has_overlap"] else "Nie"}
- **Istniejące narzędzia**: {", ".join(overlap["existing_tools"]) if overlap["existing_tools"] else "brak"}

## Notatki

{result["proposal"].get("notes", "Brak notatek")}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n   📝 Zapisano audyt: {path}")
    return path


def main():
    if not os.path.exists(PROPOSALS_PATH):
        print("❌ Brak proposals.csv. Użyj /ias-audit lub proposal_collect.py.")
        sys.exit(1)

    proposals = load_proposals()
    if not proposals:
        print("📭 Brak propozycji w proposals.csv")
        return

    all_flag = "--all" in sys.argv
    id_filter = None
    if "--id" in sys.argv:
        idx = sys.argv.index("--id")
        if len(sys.argv) > idx + 1:
            id_filter = int(sys.argv[idx + 1])

    to_audit = []
    for i, p in enumerate(proposals):
        if id_filter is not None and i != id_filter:
            continue
        if not all_flag and p.get("status") != "pending":
            continue
        to_audit.append((i, p))

    if not to_audit:
        print("ℹ️  Brak propozycji do audytu. Użyj --all by przeaudytować wszystkie.")
        return

    print(f"\n🔍 Rozpoczynam audyt {len(to_audit)} propozycji...\n")

    results = []
    for i, proposal in to_audit:
        result = analyze_proposal(proposal)

        # Zapisz do vault_writer (Obsidian template v3) zamiast data/audits
        try:
            from vault_writer import write_repo_analysis

            dm = result["decision_matrix"]
            vault_path = write_repo_analysis(
                {
                    "repo_full_name": result["repo"],
                    "repo_url": result["proposal"]["url"],
                    "primary_language": result["proposal"].get("type", "repo"),
                    "stars": 0,
                    "license": "Unknown",
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "mission": f"Propozycja: {result['repo']}",
                    "personality": result["proposal"].get("notes", "W toku"),
                    "feature_matrix": [],
                    "unique_points": [],
                    "not_what": "",
                    "strengths": [],
                    "challenges": [],
                    "inspiration": "",
                    "adoption_effort": {
                        "czas_nauki": 10 - dm["adoption_effort"],
                        "migracja": 5,
                        "testy": 5,
                        "wsparcie": 5,
                    },
                    "value_score": {
                        "nowe_funkcje": dm["gap_fit"],
                        "jakosc_vs_nasze": dm["quality"],
                        "integracje": dm["team_fit"],
                        "wydajnosc": 5,
                    },
                    "net_benefit": dm["net_benefit"],
                    "verdict": dm["verdict"].split()[0],
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
                    "notes": result["proposal"].get("notes", ""),
                    "justification": f"Net Benefit: {dm['net_benefit']} → {dm['verdict']}",
                }
            )
            print(f"\n   📝 Zapisano do vault: {vault_path}")
        except ImportError:
            save_audit(result)
        except Exception as e:
            print(f"\n   ⚠️  Vault writer error: {e}")
            save_audit(result)

        results.append((i, result))

        # Update proposals.csv
        proposals[i]["status"] = "audited"
        proposals[i]["timestamp"] = datetime.now(timezone.utc).isoformat()
        save_proposals(proposals)

    # Podsumowanie
    print(f"\n{'=' * 60}")
    print("📊 PODSUMOWANIE AUDYTU")
    print(f"{'=' * 60}")
    print(f"\nAudytowane: {len(results)}/{len(proposals)}")
    for i, r in results:
        v = r["decision_matrix"]["verdict"]
        print(
            f"  [{i}] {r['proposal']['url']} → {v} ({r['decision_matrix']['net_benefit']})"
        )

    remaining = sum(1 for p in proposals if p.get("status") == "pending")
    if remaining:
        print(f"\n⏳ Pozostało do audytu: {remaining}")
    else:
        print(f"\n✅ Wszystkie propozycje zaudytowane!")


if __name__ == "__main__":
    main()
