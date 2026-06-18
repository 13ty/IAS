#!/usr/bin/env python3
"""
orchestrator.py — Kwatermistrz: Pipeline Coordinator.

Łączy inventory_scan.py → analyzer_check.py → scout_search.py w pipeline
z checkpointami, zarządzaniem stanem i raportowaniem.

Użycie:
  python scripts/orchestrator.py --scan R:\\Dev\\MyProject
  python scripts/orchestrator.py --scan R:\\Dev\\MyProject --analyze https://github.com/fastapi/fastapi
  python scripts/orchestrator.py --scan R:\\Dev\\MyProject --skip-analyze
  python scripts/orchestrator.py --scan R:\\Dev\\MyProject --json
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

IAS_ROOT = Path(__file__).parent.parent
STATE_DIR = IAS_ROOT / "state"
STATE_FILE = STATE_DIR / "tech_stack_oracle.json"
SCRIPTS_DIR = IAS_ROOT / "scripts"


def load_state() -> dict:
    """Wczytaj stan pipeline'u."""
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "1.0.0",
        "lastUpdated": datetime.now().isoformat(),
        "currentPhase": "IDLE",
        "projectPath": "",
        "inventory": None,
        "analysis": None,
        "scout": None,
        "decisions": [],
        "history": [],
    }


def save_state(state: dict) -> None:
    """Zapisz stan pipeline'u."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["lastUpdated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def run_inventory(project_path: str) -> dict:
    """Uruchom inventory_scan.py, zwróć wynik jako dict."""
    print(f"\n{'=' * 60}")
    print(f"📦 FAZA 1: INVENTORY")
    print(f"{'=' * 60}")

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    tmp_path = tmp.name
    tmp.close()

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "inventory_scan.py"),
                project_path,
                "--json",
                "--output",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"❌ Inventory failed: {result.stderr}")
            return None

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        # Podsumowanie
        radar = data.get("radar", {})
        gaps = data.get("gaps", [])
        health = data.get("health", {})

        print(f"   Projekt: {data.get('name', 'unknown')}")
        print(f"   Ekosystemy: {', '.join(data.get('ecosystems', ['none']))}")
        print(f"   Komponenty: {health.get('totalComponents', 0)}")
        print(
            f"   Luki: {len(gaps)} ({sum(1 for g in gaps if g.get('severity') == 'high')} wysokie)"
        )
        print(f"   Health: {health.get('coverage', 0)}%")

        return data
    except subprocess.TimeoutExpired:
        print("❌ Inventory timeout (120s)")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_analyzer(repo_path: str) -> dict:
    """Uruchom analyzer_check.py, zwróć wynik jako dict."""
    print(f"\n{'=' * 60}")
    print(f"🔍 FAZA 2: ANALYZER")
    print(f"{'=' * 60}")

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    tmp_path = tmp.name
    tmp.close()

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "analyzer_check.py"),
                repo_path,
                "--json",
                "--output",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"❌ Analyzer failed: {result.stderr}")
            return None

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        ca = data.get("clean_architecture", {})
        mi = data.get("maintainability", {})

        print(f"   Repo: {data.get('name', 'unknown')}")
        print(
            f"   Clean Architecture: {ca.get('score', 0)}/100 ({ca.get('violationCount', 0)} violations)"
        )
        print(
            f"   Maintainability: {mi.get('index', 0)}/100 ({mi.get('rating', 'unknown')})"
        )
        print(f"   LOC: {mi.get('loc', 0)} | Pliki: {mi.get('fileCount', 0)}")

        return data
    except subprocess.TimeoutExpired:
        print("❌ Analyzer timeout (120s)")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def run_scout(gaps: list[str], max_results: int = 10) -> dict:
    """Uruchom scout_search.py, zwróć wynik jako dict."""
    if not gaps:
        print("ℹ️  Brak luk do scoutowania. Pomijam fazę Scout.")
        return None

    print(f"\n{'=' * 60}")
    print(f"🔎 FAZA 3: SCOUT")
    print(f"{'=' * 60}")

    gaps_str = ",".join(gaps)

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    tmp_path = tmp.name
    tmp.close()

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "scout_search.py"),
                "--gaps",
                gaps_str,
                "--max-results",
                str(max_results),
                "--json",
                "--output",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"❌ Scout failed: {result.stderr}")
            return None

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        results = data.get("results", [])
        summary = data.get("summary", {})

        print(f"   Znaleziono: {len(results)} repozytoriów")
        print(f"   Luki pokryte: {', '.join(summary.get('gaps_covered', []))}")
        if summary.get("gaps_missing"):
            print(f"   Luki bez pokrycia: {', '.join(summary['gaps_missing'])}")

        if results:
            print(f"\n   TOP 5:")
            for i, r in enumerate(results[:5], 1):
                print(
                    f"   {i}. {r.get('repo', 'unknown')} ⭐{r.get('stars', 0)} (score: {r.get('final_score', 0)})"
                )
                print(f"      Gap: {', '.join(r.get('gap_coverage', []))}")

        return data
    except subprocess.TimeoutExpired:
        print("❌ Scout timeout (60s)")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def print_report(state: dict) -> None:
    """Wygeneruj końcowy raport pipeline'u."""
    inventory = state.get("inventory")
    analysis = state.get("analysis")
    scout = state.get("scout")

    print(f"\n\n{'=' * 60}")
    print(f"📋 RAPORT KOŃCOWY — IAS KWATERNISTRZ")
    print(f"{'=' * 60}")
    print(f"   Projekt: {state.get('projectPath', 'N/A')}")
    print(f"   Data: {state.get('lastUpdated', 'N/A')}")

    if inventory:
        health = inventory.get("health", {})
        gaps = inventory.get("gaps", [])
        print(f"\n📦 INVENTORY")
        print(f"   Komponenty: {health.get('totalComponents', 0)}")
        print(f"   Luki: {len(gaps)}")
        for g in gaps:
            icon = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(
                g.get("severity", ""), "·"
            )
            print(
                f"   {icon} [{g.get('severity', '?').upper()}] {g.get('category', '?')}: {g.get('detail', '')}"
            )

    if analysis:
        ca = analysis.get("clean_architecture", {})
        mi = analysis.get("maintainability", {})
        print(f"\n🔍 ANALYZER")
        print(f"   Clean Architecture: {ca.get('score', 0)}/100")
        print(
            f"   Maintainability: {mi.get('index', 0)}/100 ({mi.get('rating', 'unknown')})"
        )

    if scout:
        results = scout.get("results", [])
        print(f"\n🔎 SCOUT")
        print(f"   Rekomendacje ({len(results)}):")
        for r in results[:5]:
            print(
                f"   • {r.get('repo', '?')} — score {r.get('final_score', 0)} — {', '.join(r.get('gap_coverage', []))}"
            )

    decisions = state.get("decisions", [])
    if decisions:
        print(f"\n📌 DECYZJE")
        for d in decisions:
            status = "✅" if d.get("approved") else "⏳"
            print(f"   {status} {d.get('action', '?')} ({d.get('phase', '?')})")

    print(f"\n{'=' * 60}")
    print(f"✅ Pipeline zakończony. Stan zapisany w: {STATE_FILE}")
    print(f"{'=' * 60}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="IAS Kwatermistrz — Pipeline Orchestrator"
    )
    parser.add_argument("--scan", type=str, help="Ścieżka projektu do skanowania")
    parser.add_argument(
        "--analyze", type=str, default=None, help="URL/ścieżka repo do analizy"
    )
    parser.add_argument(
        "--skip-analyze", action="store_true", help="Pomiń fazę Analyzer"
    )
    parser.add_argument("--skip-scout", action="store_true", help="Pomiń fazę Scout")
    parser.add_argument("--max-results", type=int, default=10, help="Max wyników Scout")
    parser.add_argument("--json", action="store_true", help="Wynik jako JSON")
    parser.add_argument("--output", type=str, help="Zapisz wynik do pliku")

    args = parser.parse_args()

    if not args.scan:
        print("❌ Użycie: python orchestrator.py --scan <path>")
        sys.exit(1)

    if not Path(args.scan).exists():
        print(f"❌ Ścieżka nie istnieje: {args.scan}")
        sys.exit(1)

    state = load_state()
    state["currentPhase"] = "INVENTORY"
    state["projectPath"] = args.scan
    save_state(state)

    # --- FAZA 1: INVENTORY ---
    inventory_result = run_inventory(args.scan)
    if inventory_result is None:
        state["currentPhase"] = "ERROR"
        save_state(state)
        sys.exit(1)

    state["inventory"] = inventory_result
    state["currentPhase"] = "CHECKPOINT_1"
    save_state(state)

    # CHECKPOINT 1: Po Inventory
    gaps = [g.get("category", "") for g in inventory_result.get("gaps", [])]
    print(f"\n⏸️  CHECKPOINT 1: Wykryto {len(gaps)} luk.")
    print(f"   Aby kontynuować z Analyzer: użyj --analyze <url>")
    print(f"   Aby pominąć Analyzer: użyj --skip-analyze")

    # --- FAZA 2: ANALYZER (opcjonalnie) ---
    analysis_result = None
    if not args.skip_analyze and args.analyze:
        state["currentPhase"] = "ANALYZER"
        save_state(state)

        # Jeśli URL → spróbuj sklonować do temp
        repo_path = args.analyze
        if args.analyze.startswith("http"):
            tmp_dir = tempfile.mkdtemp(prefix="ias-clone-")
            print(f"\n📦 Klonowanie {args.analyze} do {tmp_dir}...")
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", args.analyze, tmp_dir],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if clone_result.returncode == 0:
                repo_path = tmp_dir
            else:
                print(f"⚠️  Nie udało się sklonować: {clone_result.stderr}")
                repo_path = args.analyze  # fallback: użyj URL jako nazwy

        analysis_result = run_analyzer(repo_path)
        state["analysis"] = analysis_result
        state["currentPhase"] = "CHECKPOINT_2"
        save_state(state)

        print(f"\n⏸️  CHECKPOINT 2: Analiza zakończona.")
    elif args.skip_analyze:
        print(f"\n⏭️  Pomijam Analyzer (--skip-analyze).")

    # --- FAZA 3: SCOUT (opcjonalnie) ---
    scout_result = None
    if not args.skip_scout:
        state["currentPhase"] = "SCOUT"
        save_state(state)

        # Użyj gapów z inventory
        scout_gaps = [g.get("category", "") for g in inventory_result.get("gaps", [])]
        if analysis_result:
            # Dodaj rekomendacje z analyzer
            for rec in analysis_result.get("recommendations", []):
                scout_gaps.append(rec)

        scout_result = run_scout(scout_gaps, args.max_results)
        state["scout"] = scout_result
        state["currentPhase"] = "COMPLETE"
        save_state(state)
    else:
        state["currentPhase"] = "COMPLETE"
        save_state(state)

    # --- RAPORT ---
    if args.json:
        output = state
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Raport zapisany: {args.output}")
        else:
            print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_report(state)

    # Dodaj do historii
    state["history"].append(
        {
            "date": datetime.now().isoformat(),
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "inventory_summary": f"{len(inventory_result.get('components', []))} deps, {len(gaps)} gaps",
            "analysis_summary": f"CA: {analysis_result.get('clean_architecture', {}).get('score', 'N/A')}, MI: {analysis_result.get('maintainability', {}).get('index', 'N/A')}"
            if analysis_result
            else "skipped",
            "scout_summary": f"{len(scout_result.get('results', []))} matches"
            if scout_result
            else "skipped",
        }
    )
    save_state(state)


if __name__ == "__main__":
    main()
