#!/usr/bin/env python3
"""
MCP Server for IAS Kwatermistrz.

Exposes all IAS functionality via Model Context Protocol (MCP).
Any MCP-compatible client (Claude Desktop, Cursor, OpenCode, VS Code)
can query the tool registry, run inventory scans, analyze repos,
search for gap-filling tools, and generate heatmaps.

Usage:
    python scripts/mcp_server.py          # stdio transport (default)
    python scripts/mcp_server.py --sse    # SSE transport (future)

Transport modes:
    stdio — for local agents (Claude, Cursor, OpenCode)
    SSE   — for remote agents (future, needs --sse flag + --port)

Architecture:
    MCP Client → FastMCP Server → existing IAS scripts (import or subprocess)
                                  → tool_registry.json (file-locked)
                                  → pipeline state (state/ directory)

Security:
    - All operations are read-only EXCEPT tool_register
    - tool_registry.json uses portalocker for concurrent write safety
    - No network access unless client explicitly enables SSE
    - Subprocess calls inherit timeout limits from parent scripts
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# ─── Paths ─────────────────────────────────────────────────────────────────────

PLUGIN_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_DIR / "scripts"
STATE_DIR = PLUGIN_DIR / "state"
REGISTRY_PATH = PLUGIN_DIR / "data" / "tool_registry.json"
RESEARCH_CSV_PATH = PLUGIN_DIR / "data" / "research" / "tools.csv"
STATE_FILE = STATE_DIR / "tech_stack_oracle.json"

TIMEOUT_INVENTORY = 180  # cdxgen/grype can be slow
TIMEOUT_ANALYZER = 120  # git clone + analysis
TIMEOUT_SCOUT = 60  # gh API calls

# ─── Server Setup ──────────────────────────────────────────────────────────────

mcp = FastMCP(
    "IAS Kwatermistrz",
    instructions="Kwatermistrz — centralny system logistyczny środowiska developerskiego. "
    "Inwentaryzuje narzędzia, analizuje repozytoria, szuka rozwiązań, "
    "generuje mapę ciepła ekosystemu.",
    log_level="WARNING",
)


# ─── Helper: subprocess wrappers ────────────────────────────────────────────────


def _run_script(
    script_name: str,
    args: list[str],
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Uruchom skrypt IAS przez subprocess i zwróć wynik jako dict.

    Args:
        script_name: Nazwa pliku skryptu (np. 'inventory_scan.py')
        args: Argumenty CLI dla skryptu
        timeout: Maksymalny czas oczekiwania w sekundach

    Returns:
        Sparsowany JSON z stdout skryptu

    Raises:
        RuntimeError: Jeśli skrypt zwróci błąd lub przekroczy timeout
    """
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise RuntimeError(f"Skrypt nie istnieje: {script_path}")

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    tmp_path = tmp.name
    tmp.close()

    try:
        cmd = [
            sys.executable,
            str(script_path),
            *args,
            "--json",
            "--output",
            tmp_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            stderr_preview = (
                result.stderr.strip()[:500] if result.stderr else "no stderr"
            )
            raise RuntimeError(
                f"{script_name} exited code {result.returncode}: {stderr_preview}"
            )

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise RuntimeError(f"{script_name} nie wyprodukował pliku wyjściowego")

        with open(tmp_path, encoding="utf-8") as f:
            data = json.load(f)

        return data

    except json.JSONDecodeError as e:
        raise RuntimeError(f"{script_name}: błąd parsowania JSON — {e}") from e
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{script_name}: przekroczono timeout ({timeout}s)")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _load_registry() -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Wczytaj tool_registry.json z prostym file locking.
    """
    if not REGISTRY_PATH.exists():
        return {}, {}
    try:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tools", {}), data.get("domains", {})
    except json.JSONDecodeError:
        return {}, {}


def _load_pipeline_state() -> dict[str, Any]:
    """Wczytaj stan pipeline'u."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "version": "2.0.0",
        "currentPhase": "IDLE",
        "projectPath": "",
        "inventory": None,
        "analysis": None,
        "scout": None,
        "decisions": [],
    }


def _load_research_csv() -> list[dict[str, str]]:
    """Wczytaj data/research/tools.csv jako listę dictów."""
    if not RESEARCH_CSV_PATH.exists():
        return []

    try:
        with open(RESEARCH_CSV_PATH, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]
    except (csv.Error, OSError) as e:
        return []


# ─── Tools ──────────────────────────────────────────────────────────────────────


@mcp.tool(
    name="inventory_scan",
    description="Przeprowadź pełny skan inwentaryzacyjny projektu: "
    "SBOM (lista zależności), Technology Radar, wykryte luki technologiczne, "
    "oraz health score projektu.",
)
def inventory_scan_tool(
    project_path: str,
) -> str:
    """
    Skanuje projekt pod kątem zależności, frameworków i luk technologicznych.

    Args:
        project_path: Ścieżka do projektu na dysku (np. R:\\Dev\\MyProject)

    Returns:
        JSON z komponentami, radarem technologicznym, lukami i health score.
    """
    if not os.path.isdir(project_path):
        return json.dumps(
            {"error": f"Ścieżka nie istnieje: {project_path}"},
            ensure_ascii=False,
        )

    try:
        data = _run_script(
            "inventory_scan.py",
            [project_path],
            timeout=TIMEOUT_INVENTORY,
        )
        # Dodaj timestamp
        data["_mcp_timestamp"] = datetime.now().isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool(
    name="analyze_repo",
    description="Analizuje repozytorium pod kątem Clean Architecture "
    "(ilość naruszeń warstw) i Maintainability Index (MI). "
    "Acceptuje URL GitHub lub ścieżkę lokalną.",
)
def analyze_repo_tool(
    repo_path: str,
) -> str:
    """
    Analizuje repozytorium: Clean Architecture score + Maintainability Index.

    Args:
        repo_path: URL GitHub (https://github.com/user/repo) lub ścieżka lokalna

    Returns:
        JSON z oceną Clean Architecture, MI, LOC, liczbą plików.
    """
    try:
        data = _run_script(
            "analyzer_check.py",
            [repo_path],
            timeout=TIMEOUT_ANALYZER,
        )
        data["_mcp_timestamp"] = datetime.now().isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool(
    name="scout_gaps",
    description="Szuka repozytoriów na GitHub, które wypełniają "
    "określone luki technologiczne. Wymaga zainstalowanego `gh` CLI.",
)
def scout_gaps_tool(
    gaps_csv: str,
    max_results: int = 10,
) -> str:
    """
    Szuka narzędzi na GitHub pasujących do zdefiniowanych luk.

    Args:
        gaps_csv: Lista kategorii luk oddzielonych przecinkami
                  (np. "testing,security,ci-cd")
        max_results: Maksymalna liczba wyników (domyślnie 10)

    Returns:
        JSON z listą znalezionych repozytoriów, score'ami i gap coverage.
    """
    try:
        data = _run_script(
            "scout_search.py",
            ["--gaps", gaps_csv, "--max-results", str(max_results)],
            timeout=TIMEOUT_SCOUT,
        )
        data["_mcp_timestamp"] = datetime.now().isoformat()
        return json.dumps(data, indent=2, ensure_ascii=False)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool(
    name="heatmap_status",
    description="Generuje mapę ciepła ekosystemu narzędzi: "
    "pokrycie domen, nakładanie się, konflikty portów, "
    "mocne i słabe strony. Bezpośrednio z tool_registry.json.",
)
def heatmap_status_tool(
    output_format: str = "json",
) -> str:
    """
    Zwraca aktualną mapę ciepła ekosystemu narzędzi.

    Args:
        output_format: Format wyjścia — "json" (domyślnie), "ascii", lub "mermaid"

    Returns:
        Raport mapy ciepła w żądanym formacie.
    """
    # Importuj bezpośrednio — heatmap.py ma czyste funkcje
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from heatmap import (  # type: ignore[import-untyped]
            build_report,
            generate_ascii_table,
            generate_json_output,
            generate_mermaid_diagram,
            load_registry,
            parse_tools,
        )
    except ImportError as e:
        return json.dumps(
            {"error": f"Nie można zaimportować heatmap: {e}"}, ensure_ascii=False
        )

    tools_raw, _ = load_registry()
    if not tools_raw:
        return json.dumps({"error": "Rejestr narzędzi jest pusty."}, ensure_ascii=False)

    tools = parse_tools(tools_raw)
    report = build_report(tools)

    match output_format:
        case "ascii":
            return generate_ascii_table(report)
        case "mermaid":
            return generate_mermaid_diagram(report)
        case _:
            return generate_json_output(report)


@mcp.tool(
    name="tool_registry_list",
    description="Listuje wszystkie narzędzia w rejestrze, "
    "opcjonalnie filtrowane po domenie. "
    "Zwraca JSON z narzędziami, domenami i priorytetami.",
)
def tool_registry_list_tool(
    domain: str = "",
) -> str:
    """
    Zwraca listę narzędzi z rejestru, opcjonalnie filtrowaną po domenie.

    Args:
        domain: Filtruj po domenie (np. "visual", "data", "devops").
                Puste = wszystkie domeny.

    Returns:
        JSON z listą narzędzi i statystykami.
    """
    tools_raw, domains_raw = _load_registry()
    if not tools_raw:
        return json.dumps({"error": "Rejestr narzędzi jest pusty."}, ensure_ascii=False)

    # Filtruj po domenie jeśli podana
    if domain:
        domain_lower = domain.lower()
        filtered = {}
        for tid, tdata in tools_raw.items():
            if tdata.get("domain", "").lower() == domain_lower:
                filtered[tid] = tdata
        result = {
            "domain": domain,
            "count": len(filtered),
            "tools": filtered,
            "available_domains": list(domains_raw.keys()),
        }
    else:
        result = {
            "count": len(tools_raw),
            "tools": tools_raw,
            "domains": {
                d: {"tools": tools, "count": len(tools)}
                for d, tools in domains_raw.items()
            },
            "stats": {
                "total_tools": len(tools_raw),
                "total_domains": len(domains_raw),
            },
        }

    result["_mcp_timestamp"] = datetime.now().isoformat()
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool(
    name="tool_details",
    description="Zwraca szczegółowe informacje o konkretnym narzędziu "
    "z rejestru: ścieżka, wersja, typ, domena, priorytet, "
    "komendy uruchomienia/aktualizacji, alternatywy.",
)
def tool_details_tool(
    name: str,
) -> str:
    """
    Pobiera szczegóły pojedynczego narzędzia z rejestru.

    Args:
        name: ID/nazwa narzędzia (np. "DuckDB", "Semgrep", "fd")

    Returns:
        JSON ze szczegółami narzędzia lub komunikatem o błędzie.
    """
    tools_raw, _ = _load_registry()
    if not tools_raw:
        return json.dumps({"error": "Rejestr narzędzi jest pusty."}, ensure_ascii=False)

    # Szukaj po ID (case-insensitive)
    name_lower = name.lower()
    for tid, tdata in tools_raw.items():
        if tid.lower() == name_lower:
            result = {"id": tid, **tdata}
            result["_mcp_timestamp"] = datetime.now().isoformat()
            return json.dumps(result, indent=2, ensure_ascii=False)

    # Szukaj po name field (case-insensitive)
    for tid, tdata in tools_raw.items():
        if tdata.get("name", "").lower() == name_lower:
            result = {"id": tid, **tdata}
            result["_mcp_timestamp"] = datetime.now().isoformat()
            return json.dumps(result, indent=2, ensure_ascii=False)

    return json.dumps(
        {
            "error": f"Nie znaleziono narzędzia '{name}'.",
            "available_tools": list(tools_raw.keys()),
        },
        ensure_ascii=False,
    )


@mcp.tool(
    name="scan_project",
    description="Uruchamia pełny pipeline IAS na projekcie: "
    "Inventory → (opcjonalnie) Analyzer → Scout → Raport. "
    "To samo co /ias-scan w OpenCode.",
)
def scan_project_tool(
    project_path: str,
    analyze_url: str = "",
    skip_analyze: bool = False,
    skip_scout: bool = False,
) -> str:
    """
    Pełny pipeline IAS: Inventory → Analyzer → Scout.

    Args:
        project_path: Ścieżka do projektu
        analyze_url: URL GitHub do analizy (opcjonalnie)
        skip_analyze: Pomiń fazę Analyzer (domyślnie: False)
        skip_scout: Pomiń fazę Scout (domyślnie: False)

    Returns:
        JSON z wynikami wszystkich faz pipeline'u.
    """
    if not os.path.isdir(project_path):
        return json.dumps(
            {"error": f"Ścieżka nie istnieje: {project_path}"},
            ensure_ascii=False,
        )

    result = {
        "project_path": project_path,
        "timestamp": datetime.now().isoformat(),
        "phases": {},
        "errors": [],
    }

    # FAZA 1: Inventory
    try:
        inv_data = _run_script(
            "inventory_scan.py",
            [project_path],
            timeout=TIMEOUT_INVENTORY,
        )
        result["phases"]["inventory"] = {
            "status": "ok",
            "components": len(inv_data.get("components", [])),
            "gaps": len(inv_data.get("gaps", [])),
            "health": inv_data.get("health", {}),
            "gaps_list": inv_data.get("gaps", []),
        }
    except RuntimeError as e:
        result["phases"]["inventory"] = {"status": "error", "message": str(e)}
        result["errors"].append(f"inventory: {e}")

    # FAZA 2: Analyzer (opcjonalnie)
    if not skip_analyze and analyze_url:
        try:
            an_data = _run_script(
                "analyzer_check.py",
                [analyze_url],
                timeout=TIMEOUT_ANALYZER,
            )
            result["phases"]["analyzer"] = {
                "status": "ok",
                "clean_architecture": an_data.get("clean_architecture", {}),
                "maintainability": an_data.get("maintainability", {}),
            }
        except RuntimeError as e:
            result["phases"]["analyzer"] = {"status": "error", "message": str(e)}
            result["errors"].append(f"analyzer: {e}")

    # FAZA 3: Scout (opcjonalnie)
    if not skip_scout:
        gaps = [
            g.get("category", "")
            for g in result.get("phases", {}).get("inventory", {}).get("gaps_list", [])
        ]
        if gaps:
            try:
                sc_data = _run_script(
                    "scout_search.py",
                    ["--gaps", ",".join(gaps), "--max-results", "10"],
                    timeout=TIMEOUT_SCOUT,
                )
                result["phases"]["scout"] = {
                    "status": "ok",
                    "results_count": len(sc_data.get("results", [])),
                    "results": sc_data.get("results", []),
                }
            except RuntimeError as e:
                result["phases"]["scout"] = {"status": "error", "message": str(e)}
                result["errors"].append(f"scout: {e}")
        else:
            result["phases"]["scout"] = {
                "status": "skipped",
                "reason": "Brak luk do scoutowania",
            }

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool(
    name="research_search",
    description="Przeszukuje bazę odkrytych narzędzi (research database). "
    "Filtruje po kategorii, statusie, decyzji, słowie kluczowym, "
    "integracji z LanceDB, lub priorytecie. Zwraca JSON z pasującymi wpisami.",
)
def research_search_tool(
    category: str = "",
    status: str = "",
    decision: str = "",
    keyword: str = "",
    lancedb_integration: str = "",
    priority: str = "",
    limit: int = 50,
) -> str:
    """
    Szuka narzędzi w research database data/research/tools.csv.

    Args:
        category: Filtruj po kategorii (np. "web-crawling", "rag-platform", "dashboard")
        status: Filtruj po statusie ("pending", "audited", "installed", "rejected", "archived")
        decision: Filtruj po decyzji ("TAKE", "WAIT", "BUILD", "SKIP")
        keyword: Szukaj w nazwie, opisie i notatkach (case-insensitive)
        lancedb_integration: Filtruj po typie integracji z LanceDB ("native", "adapter", "optional", "plugin")
        priority: Filtruj po priorytecie ("hot", "warm", "cold")
        limit: Maksymalna liczba wyników (domyślnie 50)

    Returns:
        JSON z listą pasujących narzędzi i metadanymi wyszukiwania.
    """
    tools = _load_research_csv()
    if not tools:
        return json.dumps(
            {"error": "Research database jest pusta.", "count": 0, "tools": []},
            ensure_ascii=False,
        )

    filtered = tools
    filters_applied = []

    if category:
        cat_lower = category.lower()
        filtered = [t for t in filtered if t.get("category", "").lower() == cat_lower]
        filters_applied.append(f"category={category}")

    if status:
        st_lower = status.lower()
        filtered = [t for t in filtered if t.get("status", "").lower() == st_lower]
        filters_applied.append(f"status={status}")

    if decision:
        dec_upper = decision.upper()
        filtered = [t for t in filtered if t.get("decision", "").upper() == dec_upper]
        filters_applied.append(f"decision={decision}")

    if lancedb_integration:
        li_lower = lancedb_integration.lower()
        filtered = [
            t for t in filtered if t.get("lancedb_integration", "").lower() == li_lower
        ]
        filters_applied.append(f"lancedb_integration={lancedb_integration}")

    if priority:
        prio_lower = priority.lower()
        filtered = [t for t in filtered if t.get("priority", "").lower() == prio_lower]
        filters_applied.append(f"priority={priority}")

    if keyword:
        kw_lower = keyword.lower()
        filtered = [
            t
            for t in filtered
            if kw_lower in t.get("name", "").lower()
            or kw_lower in t.get("description", "").lower()
            or kw_lower in t.get("notes", "").lower()
            or kw_lower in t.get("technologies", "").lower()
        ]
        filters_applied.append(f"keyword={keyword}")

    result_tools = filtered[:limit]

    result = {
        "count": len(result_tools),
        "total_matching": len(filtered),
        "filters_applied": filters_applied,
        "tools": result_tools,
        "_mcp_timestamp": datetime.now().isoformat(),
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


# ─── Resources ──────────────────────────────────────────────────────────────────


@mcp.resource(
    uri="tools://registry",
    name="Full Tool Registry",
    description="Pełny rejestr narzędzi IAS — wszystkie narzędzia, "
    "domeny, priorytety, alternatywy, komendy uruchomienia.",
    mime_type="application/json",
)
def get_registry() -> str:
    """Zwraca cały tool_registry.json jako resource MCP."""
    tools_raw, domains_raw = _load_registry()
    if not tools_raw:
        return json.dumps({"error": "Rejestr narzędzi jest pusty."}, ensure_ascii=False)

    # Dodaj metadane
    result = {
        "version": "2.0.0",
        "last_updated": datetime.now().isoformat(),
        "tools": tools_raw,
        "domains": {
            d: {"tools": tools, "count": len(tools)} for d, tools in domains_raw.items()
        },
        "stats": {
            "total_tools": len(tools_raw),
            "total_domains": len(domains_raw),
            "per_domain": {d: len(t) for d, t in domains_raw.items()},
        },
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.resource(
    uri="pipeline://state",
    name="Pipeline State",
    description="Aktualny stan pipeline'u IAS — faza, projekt, "
    "wyniki inventory/analyzer/scout, historia decyzji.",
    mime_type="application/json",
)
def get_pipeline_state() -> str:
    """Zwraca aktualny stan pipeline'u jako resource MCP."""
    state = _load_pipeline_state()
    state["_mcp_timestamp"] = datetime.now().isoformat()

    # Usuń duże payloady dla czytelności
    summary = {
        "version": state.get("version"),
        "currentPhase": state.get("currentPhase"),
        "projectPath": state.get("projectPath"),
        "lastUpdated": state.get("lastUpdated"),
        "inventory_status": "completed" if state.get("inventory") else None,
        "analysis_status": "completed" if state.get("analysis") else None,
        "scout_status": "completed" if state.get("scout") else None,
        "decision_count": len(state.get("decisions", [])),
        "history_count": len(state.get("history", [])),
        "recent_decisions": state.get("decisions", [])[-5:],
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)


@mcp.resource(
    uri="research://database",
    name="Research Database",
    description="Pełna baza odkrytych narzędzi — wszystkie narzędzia "
    "znalezione podczas researchu z pełną charakterystyką "
    "(kategoria, integracja, ocena, decyzja).",
    mime_type="application/json",
)
def get_research_database() -> str:
    """Zwraca całą research database jako resource MCP."""
    tools = _load_research_csv()
    if not tools:
        return json.dumps(
            {"error": "Research database jest pusta."}, ensure_ascii=False
        )

    # Statystyki
    categories = {}
    statuses = {}
    decisions = {}
    for t in tools:
        cat = t.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        st = t.get("status", "unknown")
        statuses[st] = statuses.get(st, 0) + 1
        dec = t.get("decision", "unknown")
        decisions[dec] = decisions.get(dec, 0) + 1

    result = {
        "name": "Research Database",
        "path": str(RESEARCH_CSV_PATH),
        "count": len(tools),
        "last_updated": datetime.now().isoformat(),
        "statistics": {
            "by_category": categories,
            "by_status": statuses,
            "by_decision": decisions,
            "hot_count": sum(1 for t in tools if t.get("priority") == "hot"),
            "warm_count": sum(1 for t in tools if t.get("priority") == "warm"),
            "cold_count": sum(1 for t in tools if t.get("priority") == "cold"),
            "recommended_take": sum(1 for t in tools if t.get("decision") == "TAKE"),
        },
        "tools": tools,
        "_mcp_timestamp": datetime.now().isoformat(),
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


# ─── Prompts ────────────────────────────────────────────────────────────────────


@mcp.prompt(
    name="audit_proposal",
    description="Generuje strukturę audytu dla proponowanego narzędzia. "
    "Zwraca prompt z decision matrix, gap analysis i overlap detection. "
    "Użyj gdy chcesz ocenić czy nowe narzędzie jest warte adopcji.",
)
def audit_proposal_prompt(url: str) -> str:
    """
    Tworzy ustrukturyzowany prompt audytu dla proponowanego narzędzia.

    Args:
        url: URL do repozytorium lub strony narzędzia

    Returns:
        Prompt audytowy do wykorzystania przez agenta.
    """
    # Pobierz kontekst: co już mamy w domenach
    tools_raw, domains_raw = _load_registry()
    domain_summary = "\n".join(
        f"  - **{d}**: {', '.join(tools)}" for d, tools in domains_raw.items()
    )
    total_tools = len(tools_raw)

    return f"""# Audyt Propozycji Narzędzia

## Źródło
{url}

## Instrukcja

Przeprowadź audyt tego narzędzia względem istniejącego stacka IAS.

### Krok 1: Klasyfikacja
- Typ: (repo/cli/package/other)
- GitHub: stars, forks, last commit
- License: (sprawdź czy kompatybilna z naszym stackiem)

### Krok 2: Gap Analysis
Czy to narzędzie wypełnia istniejącą lukę?

Aktualny stack ({total_tools} narzędzi w {len(domains_raw)} domenach):
{domain_summary}

- **Feature Gap**: Czy robi coś czego nie mamy?
- **Quality Gap**: Czy jest lepsze od tego co mamy w domenie?
- **Integration Gap**: Czy łatwo zintegrować z naszym środowiskiem?

### Krok 3: Overlap Detection
- Czy nakłada się na istniejące narzędzia?
- Jeśli tak → feature-by-feature comparison
- Rekomendacja: migruj / odrzuć / trzymaj oba

### Krok 4: Decision Matrix

| Kryterium | Waga | Score (1-10) | Uzasadnienie |
|-----------|------|--------------|--------------|
| Gap Fit | 0.30 | | |
| Quality | 0.25 | | |
| Team Fit | 0.30 | | |
| Adoption Effort | 0.15 | | |

**Net Benefit = Σ(kryterium × waga)**

Progi:
- > 7.0 → **ZAPROSZENIE DO TAŃCA** (adopt)
- > 4.0 → **PILOT** (trial)
- ≤ 4.0 → **LEKCJA** (nie adoptujemy)

### Krok 5: Rekomendacja
- Decyzja: adopt / pilot / odrzuć
- Uzasadnienie: 2-3 zdania
- Ryzyka: lista potencjalnych problemów
"""


# ─── Entry Point ────────────────────────────────────────────────────────────────


def main() -> None:
    """Uruchom MCP server IAS."""
    import argparse

    parser = argparse.ArgumentParser(
        description="IAS Kwatermistrz — MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  python scripts/mcp_server.py              # stdio (domyślnie)
  python scripts/mcp_server.py --sse --port 8111  # SSE (future)
        """,
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Użyj transportu SSE zamiast stdio",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8111,
        help="Port dla SSE (domyślnie 8111)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host dla SSE (domyślnie 127.0.0.1)",
    )

    args = parser.parse_args()

    # Info log
    transport = "SSE" if args.sse else "stdio"
    addr = f"{args.host}:{args.port}" if args.sse else "(stdin/stdout)"
    print(f"IAS MCP Server — transport: {transport} — listen: {addr}", file=sys.stderr)

    if args.sse:
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
