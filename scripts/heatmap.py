#!/usr/bin/env python3
"""
heatmap.py — Kwatermistrz Heat Map 4D

Generuje wielowymiarową mapę ciepła ekosystemu narzędzi IAS.
Zamiast płaskich kategorii — macierz 4 wymiarów (Warstwa, Funkcja, Domena, Wzorzec).

Widoki:
    summary         Podsumowanie + kluczowe metryki (domyślny)
    stack           Macierz pokrycia warstw (A) × domen (C)
    functions       Macierz pokrycia funkcji (B) × domen (C)
    overlap         Macierz nakładania — które narzędzia naprawdę konkurują
    integration     Graf połączeń między sąsiednimi warstwami
    gaps            Lista luk per (A, B, C, D)

Użycie:
    python heatmap.py                        # Widok summary (domyślnie)
    python heatmap.py --view stack           # Stack Coverage
    python heatmap.py --view gaps            # Gaps only
    python heatmap.py --json                 # Wyjście JSON
    python heatmap.py --output report.md     # Zapis do pliku
    python heatmap.py --check-ports          # Tylko konflikty portów
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Ścieżki ─────────────────────────────────────────────────────────────────────

PLUGIN_DIR = Path(__file__).parent.parent
REGISTRY_PATH = PLUGIN_DIR / "data" / "tool_registry.json"
TAXONOMY_PATH = PLUGIN_DIR / "data" / "taxonomy_mapping.json"
ENVY_PATH = PLUGIN_DIR / "backend" / ".envy"

# ─── Stałe taksonomii ────────────────────────────────────────────────────────────

LAYERS = {
    "A0": "Physical Storage",
    "A1": "Data Store",
    "A2": "Vector Store",
    "A3": "Search Engine",
    "A4": "Index / Cache",
    "A5": "Embedding / ML",
    "A6": "RAG Framework",
    "A7": "Agent Framework",
    "A8": "Application",
}

FUNCTIONS = {
    "B0": "Capture",
    "B1": "Organize",
    "B2": "Store",
    "B3": "Retrieve",
    "B4": "Analyze",
    "B5": "Publish",
    "B6": "Collaborate",
}

DOMAINS_4D = {
    "C0": "System / Infra",
    "C1": "Development",
    "C2": "Data / Analytics",
    "C3": "AI / ML",
    "C4": "PKM",
    "C5": "Reading / Research",
    "C6": "Design / Creative",
    "C7": "Project Management",
    "C8": "Content Management",
    "C9": "Communication",
}

PATTERNS = {
    "D0": "Document Store",
    "D1": "Relational DB",
    "D2": "Full-text Search",
    "D3": "Vector Search",
    "D4": "Knowledge Graph",
    "D5": "RAG",
    "D6": "Agent Memory",
    "D7": "Event Sourcing",
    "D8": "ETL / Pipeline",
    "D9": "Pub / Sub",
    "D10": "Code Analysis",
    "D11": "File Search",
    "D12": "Document Render",
}

ALL_DIMS = {
    "layer": LAYERS,
    "function": FUNCTIONS,
    "domain": DOMAINS_4D,
    "pattern": PATTERNS,
}


# ─── Struktury danych ────────────────────────────────────────────────────────────


@dataclass
class ToolInfo:
    """Reprezentacja narzędzia z rejestru (płaska)."""

    id: str
    name: str
    version: str
    tool_type: str
    domain: str
    priority: str
    status: str
    location: str
    run_command: str
    update_command: str
    alternatives: List[str]
    description: str


@dataclass
class Taxonomy4D:
    """Klasyfikacja narzędzia w 4 wymiarach."""

    layer_primary: str
    layer_secondary: List[str]
    function_primary: str
    function_secondary: List[str]
    domain_primary: str
    domain_secondary: List[str]
    pattern_primary: str
    pattern_secondary: List[str]

    @property
    def all_layers(self) -> List[str]:
        return [self.layer_primary] + self.layer_secondary

    @property
    def all_functions(self) -> List[str]:
        return [self.function_primary] + self.function_secondary

    @property
    def all_domains(self) -> List[str]:
        return [self.domain_primary] + self.domain_secondary

    @property
    def all_patterns(self) -> List[str]:
        return [self.pattern_primary] + self.pattern_secondary


@dataclass
class Overlap4D:
    """Nakładanie wykryte przez wspólne wymiary 4D."""

    severity: str  # full | partial | complementary
    tools: List[str]
    shared: Dict[str, Any]  # primary_match + secondary dicts
    verdict: str


@dataclass
class Gap4D:
    """Luka w ekosystemie — brak narzędzia w konkretnej komórce (A,B,C,D)."""

    layer: str
    function: str
    domain: str
    pattern: str
    severity: str  # critical | moderate | notable
    description: str


@dataclass
class DomainStats:
    """Statystyki dla pojedynczej domeny (płaskiej)."""

    name: str
    tools: List[ToolInfo] = field(default_factory=list)
    hot_count: int = 0
    warm_count: int = 0
    cold_count: int = 0

    @property
    def total(self) -> int:
        return len(self.tools)

    @property
    def is_well_covered(self) -> bool:
        return self.total >= 3

    @property
    def is_gap(self) -> bool:
        return self.total <= 1


@dataclass
class OverlapGroup:
    """Grupa narzędzi mających wspólne alternatywy (stary model)."""

    domain: str
    tools: List[str]
    common_alternatives: List[str]


@dataclass
class PortConflict:
    """Wykryty konflikt portów."""

    port: int
    tools: List[str]
    source: str  # 'registry' lub 'envy'


@dataclass
class HeatMapReport4D:
    """Raport mapy ciepła — wzbogacony o 4D."""

    timestamp: str
    tools_count: int
    priority_distribution: Dict[str, int]

    # Podsumowanie (zachowane dla kompaty)
    domains_flat: Dict[str, DomainStats]
    overlaps_flat: List[OverlapGroup]
    port_conflicts: List[PortConflict]

    # Nowe 4D
    taxonomy: Dict[str, Taxonomy4D]
    stack_matrix: Dict[str, Dict[str, List[str]]]  # layer -> {domain: [tools]}
    function_matrix: Dict[str, Dict[str, List[str]]]  # function -> {domain: [tools]}
    overlaps_4d: List[Overlap4D]
    gaps: List[Gap4D]

    coverage_score: float
    overlap_score: float


# ─── Loadery ──────────────────────────────────────────────────────────────────────


def parse_ini_file(path: Path) -> Dict[str, Dict[str, str]]:
    config: Dict[str, Dict[str, str]] = {}
    current_section = "default"
    if not path.exists():
        return config
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].lower()
            config[current_section] = {}
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            config.setdefault(current_section, {})[key.strip()] = val.strip()
    return config


def get_used_ports() -> List[int]:
    envy = parse_ini_file(ENVY_PATH)
    ext = envy.get("external_dependencies", {})
    ports: List[int] = []
    for key, val in ext.items():
        if "port" in key.lower():
            try:
                ports.append(int(val))
            except ValueError:
                pass
    return ports


def load_registry() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        print(f"Błąd: Nie znaleziono rejestru: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Błąd JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    return data.get("tools", {}), data.get("domains", {})


def load_taxonomy() -> Dict[str, Any]:
    if not TAXONOMY_PATH.exists():
        print(
            f"Brak taksonomii: {TAXONOMY_PATH}. Uruchom najpierw klasyfikator.",
            file=sys.stderr,
        )
        return {}
    try:
        data = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
        return data.get("tools", {})
    except json.JSONDecodeError:
        return {}


def parse_tools(tools_raw: Dict[str, Any]) -> List[ToolInfo]:
    tools: List[ToolInfo] = []
    for tool_id, data in tools_raw.items():
        tools.append(
            ToolInfo(
                id=tool_id,
                name=data.get("name", tool_id),
                version=data.get("version", "unknown"),
                tool_type=data.get("type", "unknown"),
                domain=data.get("domain", "unknown"),
                priority=data.get("priority", "cold"),
                status=data.get("status", "inactive"),
                location=data.get("location", ""),
                run_command=data.get("run_command", ""),
                update_command=data.get("update_command", ""),
                alternatives=data.get("alternatives", []),
                description=data.get("description", ""),
            )
        )
    return tools


def parse_taxonomy(raw: Dict[str, Any]) -> Dict[str, Taxonomy4D]:
    result: Dict[str, Taxonomy4D] = {}
    for tool_id, data in raw.items():
        t = data.get("taxonomy", {})
        result[tool_id] = Taxonomy4D(
            layer_primary=t.get("layer", {}).get("primary", "A8"),
            layer_secondary=t.get("layer", {}).get("secondary", []),
            function_primary=t.get("function", {}).get("primary", "B0"),
            function_secondary=t.get("function", {}).get("secondary", []),
            domain_primary=t.get("domain", {}).get("primary", "C0"),
            domain_secondary=t.get("domain", {}).get("secondary", []),
            pattern_primary=t.get("pattern", {}).get("primary", "D0"),
            pattern_secondary=t.get("pattern", {}).get("secondary", []),
        )
    return result


# ─── Analizy 4D ───────────────────────────────────────────────────────────────────


def build_stack_matrix(
    taxonomies: Dict[str, Taxonomy4D],
) -> Dict[str, Dict[str, List[str]]]:
    """Layer × Domain: które narzędzia pokrywają którą warstwę w której domenie."""
    matrix: Dict[str, Dict[str, List[str]]] = {}
    for code in LAYERS:
        matrix[code] = {}
        for dcode in DOMAINS_4D:
            matrix[code][dcode] = []

    for tool_id, tax in taxonomies.items():
        for layer in tax.all_layers:
            for domain in tax.all_domains:
                if layer in matrix and domain in matrix[layer]:
                    matrix[layer][domain].append(tool_id)

    return matrix


def build_function_matrix(
    taxonomies: Dict[str, Taxonomy4D],
) -> Dict[str, Dict[str, List[str]]]:
    """Function × Domain: które narzędzia pełnią którą funkcję w której domenie."""
    matrix: Dict[str, Dict[str, List[str]]] = {}
    for code in FUNCTIONS:
        matrix[code] = {}
        for dcode in DOMAINS_4D:
            matrix[code][dcode] = []

    for tool_id, tax in taxonomies.items():
        for func in tax.all_functions:
            for domain in tax.all_domains:
                if func in matrix and domain in matrix[func]:
                    matrix[func][domain].append(tool_id)

    return matrix


def detect_overlaps_4d(taxonomies: Dict[str, Taxonomy4D]) -> List[Overlap4D]:
    """Wykryj nakładania z priorytetem na DOMAIN.

    FULL: ta sama domena primary + (funkcja LUB wzorzec) — konkurenci.
    PARTIAL: ta sama domena ALBO (funkcja + wzorzec) — sąsiedzi.
    COMPLEMENTARY: 1 primary zgodny.
    """
    overlaps: List[Overlap4D] = []
    tool_ids = list(taxonomies.keys())

    for i in range(len(tool_ids)):
        for j in range(i + 1, len(tool_ids)):
            a_id, b_id = tool_ids[i], tool_ids[j]
            ta = taxonomies[a_id]
            tb = taxonomies[b_id]

            both_domain = ta.domain_primary == tb.domain_primary
            both_function = ta.function_primary == tb.function_primary
            both_layer = ta.layer_primary == tb.layer_primary
            both_pattern = ta.pattern_primary == tb.pattern_primary

            primary_count = sum([both_layer, both_function, both_domain, both_pattern])

            shared_layer = set(ta.all_layers) & set(tb.all_layers)
            shared_func = set(ta.all_functions) & set(tb.all_functions)
            shared_domain = set(ta.all_domains) & set(tb.all_domains)
            shared_pattern = set(ta.all_patterns) & set(tb.all_patterns)

            if both_domain and (both_function or both_pattern):
                severity = "full"
                if both_function and both_pattern:
                    verdict = "KONKURENCJA — ta sama domena, funkcja i wzorzec"
                elif both_function:
                    verdict = "KONKURENCJA — ta sama domena i funkcja, inny wzorzec"
                else:
                    verdict = "KONKURENCJA — ta sama domena i wzorzec, inna funkcja"
            elif both_domain:
                severity = "partial"
                verdict = "SASIEDZTWO — ta sama domena, rozna funkcja i wzorzec"
            elif both_function and both_pattern:
                severity = "partial"
                verdict = "SASIEDZTWO — ta sama funkcja i wzorzec, rozne domeny"
            elif primary_count >= 2:
                severity = "partial"
                verdict = f"SASIEDZTWO — {primary_count}/4 primary zgodne"
            elif primary_count >= 1:
                severity = "complementary"
                verdict = f"KOMPLEMENTARNE — 1 primary zgodny"
            else:
                continue

            overlaps.append(
                Overlap4D(
                    severity=severity,
                    tools=[a_id, b_id],
                    shared={
                        "primary_match": {
                            "layer": ta.layer_primary if both_layer else None,
                            "function": ta.function_primary if both_function else None,
                            "domain": ta.domain_primary if both_domain else None,
                            "pattern": ta.pattern_primary if both_pattern else None,
                        },
                        "secondary": {
                            "layer": sorted(shared_layer - {ta.layer_primary}),
                            "function": sorted(shared_func - {ta.function_primary}),
                            "domain": sorted(shared_domain - {ta.domain_primary}),
                            "pattern": sorted(shared_pattern - {ta.pattern_primary}),
                        },
                    },
                    verdict=verdict,
                )
            )

    severity_order = {"full": 0, "partial": 1, "complementary": 2}
    overlaps.sort(key=lambda o: severity_order.get(o.severity, 9))
    return overlaps


def detect_gaps(
    stack_matrix: Dict[str, Dict[str, List[str]]],
    function_matrix: Dict[str, Dict[str, List[str]]],
) -> List[Gap4D]:
    """Wykryj luki — komórki (A,B,C,D) bez narzędzi."""
    gaps: List[Gap4D] = []

    # Krytyczne: AI/ML stack (C3) bez A2, A5, A6, A7
    for layer in ["A2", "A5", "A6", "A7"]:
        if (
            layer in stack_matrix
            and "C3" in stack_matrix[layer]
            and not stack_matrix[layer]["C3"]
        ):
            gaps.append(
                Gap4D(
                    layer=layer,
                    function="B3",
                    domain="C3",
                    pattern="D3",
                    severity="critical",
                    description=f"Brak {LAYERS.get(layer, layer)} w domenie AI/ML — blokuje RAG pipeline",
                )
            )

    # Search Engine (A3)
    for domain in ["C0", "C1", "C3"]:
        if (
            "A3" in stack_matrix
            and domain in stack_matrix["A3"]
            and not stack_matrix["A3"][domain]
        ):
            gaps.append(
                Gap4D(
                    layer="A3",
                    function="B3",
                    domain=domain,
                    pattern="D2",
                    severity="critical" if domain in ("C0", "C3") else "moderate",
                    description=f"Brak Search Engine (A3) w domenie {DOMAINS_4D.get(domain, domain)}",
                )
            )

    # Graph DB (A1/D4)
    if (
        "A1" in stack_matrix
        and "C3" in stack_matrix["A1"]
        and not stack_matrix["A1"]["C3"]
    ):
        gaps.append(
            Gap4D(
                layer="A1",
                function="B2",
                domain="C3",
                pattern="D4",
                severity="moderate",
                description="Brak Graph Database w AI/ML — potrzebne do Knowledge Graphs",
            )
        )

    # Collaboration (B6) — kompletnie puste
    for domain in DOMAINS_4D:
        if (
            "B6" in function_matrix
            and domain in function_matrix["B6"]
            and not function_matrix["B6"][domain]
        ):
            gaps.append(
                Gap4D(
                    layer="A8",
                    function="B6",
                    domain=domain,
                    pattern="D9",
                    severity="notable",
                    description=f"Brak narzędzi Collaboration (B6) — cisza we wszystkich domenach",
                )
            )
            break  # tylko jeden wpis

    # Capture (B0) — tylko Voice-OpenCode
    capture_count = sum(
        1
        for d in DOMAINS_4D
        if "B0" in function_matrix and function_matrix["B0"].get(d)
    )
    if capture_count <= 1:
        gaps.append(
            Gap4D(
                layer="A8",
                function="B0",
                domain="C1",
                pattern="D0",
                severity="moderate",
                description="Tylko Voice-OpenCode w B0 Capture — brak narzędzi do scrapingu, webhooków, importu",
            )
        )

    return gaps


def extract_ports_from_command(command: str) -> List[int]:
    ports: List[int] = []
    pattern = re.compile(r"[\s:](\d{4,5})(?:\s|/|$)")
    for match in pattern.finditer(command):
        try:
            port = int(match.group(1))
            if 1024 <= port <= 65535:
                ports.append(port)
        except ValueError:
            pass
    return ports


def detect_port_conflicts(tools: List[ToolInfo]) -> List[PortConflict]:
    conflicts: List[PortConflict] = []
    envy_ports = get_used_ports()
    registry_ports: Dict[int, List[str]] = {}
    for tool in tools:
        ports = extract_ports_from_command(tool.run_command)
        for port in ports:
            registry_ports.setdefault(port, []).append(tool.id)
    for port, tool_ids in registry_ports.items():
        if len(tool_ids) > 1:
            conflicts.append(PortConflict(port=port, tools=tool_ids, source="registry"))
    for port in envy_ports:
        if port in registry_ports:
            conflicts.append(
                PortConflict(port=port, tools=registry_ports[port], source="envy")
            )
    return conflicts


def analyze_domains_flat(tools: List[ToolInfo]) -> Dict[str, DomainStats]:
    domains: Dict[str, DomainStats] = {}
    for tool in tools:
        if tool.domain not in domains:
            domains[tool.domain] = DomainStats(name=tool.domain)
        domains[tool.domain].tools.append(tool)
        if tool.priority == "hot":
            domains[tool.domain].hot_count += 1
        elif tool.priority == "warm":
            domains[tool.domain].warm_count += 1
        else:
            domains[tool.domain].cold_count += 1
    return domains


def detect_overlaps_flat(tools: List[ToolInfo]) -> List[OverlapGroup]:
    overlaps: List[OverlapGroup] = []
    processed: set = set()
    by_domain: Dict[str, List[ToolInfo]] = {}
    for tool in tools:
        by_domain.setdefault(tool.domain, []).append(tool)
    for domain, domain_tools in by_domain.items():
        for i, tool_a in enumerate(domain_tools):
            if tool_a.id in processed:
                continue
            group_tools = [tool_a]
            common_alts = set(tool_a.alternatives)
            for tool_b in domain_tools[i + 1 :]:
                if tool_b.id in processed:
                    continue
                shared = set(tool_a.alternatives) & set(tool_b.alternatives)
                if shared:
                    group_tools.append(tool_b)
                    common_alts &= shared
            if len(group_tools) > 1:
                overlaps.append(
                    OverlapGroup(
                        domain=domain,
                        tools=[t.id for t in group_tools],
                        common_alternatives=sorted(common_alts),
                    )
                )
                for t in group_tools:
                    processed.add(t.id)
    return overlaps


def analyze_priorities(tools: List[ToolInfo]) -> Dict[str, int]:
    dist = {"hot": 0, "warm": 0, "cold": 0}
    for tool in tools:
        if tool.priority in dist:
            dist[tool.priority] += 1
    return dist


# ─── Generatory widoków ──────────────────────────────────────────────────────────


def render_stack_coverage(report: HeatMapReport4D) -> str:
    """Macierz Layer × Domain — które warstwy są pokryte w której domenie."""
    lines: List[str] = []
    lines.append("=== Stack Coverage (Layer × Domain) ===")
    lines.append("")

    # Header
    domain_codes = list(DOMAINS_4D.keys())
    header = f"{'Layer':<6} " + "  ".join(f"{d:<12}" for d in domain_codes)
    lines.append(header)
    lines.append("-" * len(header))

    for layer_code, layer_name in LAYERS.items():
        row = f"{layer_code:<6} "
        for dcode in domain_codes:
            tools_in_cell = report.stack_matrix.get(layer_code, {}).get(dcode, [])
            if not tools_in_cell:
                row += f"{'░░░':<12} "  # empty
            elif len(tools_in_cell) == 1:
                row += f"{'█' + '░░':<12} "  # single tool
            elif len(tools_in_cell) >= 3:
                row += f"{'███':<12} "  # well covered
            else:
                row += f"{'██' + '░':<12} "  # partial
        lines.append(row)

    lines.append("")
    lines.append("   ░░░ brak    █░░ 1 tool    ██░ 2 tools    ███ 3+")
    lines.append("")

    # Legend per layer
    lines.append("Warstwy:")
    for code, name in LAYERS.items():
        populated = sum(
            1 for d in DOMAINS_4D if report.stack_matrix.get(code, {}).get(d, [])
        )
        tools_here = set()
        for d in DOMAINS_4D:
            tools_here.update(report.stack_matrix.get(code, {}).get(d, []))
        lines.append(
            f"  {code} {name:<20} {len(tools_here):>2} narzędzi w {populated} domenach"
        )

    return "\n".join(lines)


def render_function_coverage(report: HeatMapReport4D) -> str:
    """Macierz Function × Domain — które funkcje są dostępne w której domenie."""
    lines: List[str] = []
    lines.append("=== Function Coverage (Function × Domain) ===")
    lines.append("")

    domain_codes = list(DOMAINS_4D.keys())
    header = f"{'Funkcja':<6} " + "  ".join(f"{d:<12}" for d in domain_codes)
    lines.append(header)
    lines.append("-" * len(header))

    for func_code, func_name in FUNCTIONS.items():
        row = f"{func_code:<6} "
        for dcode in domain_codes:
            tools_in_cell = report.function_matrix.get(func_code, {}).get(dcode, [])
            if not tools_in_cell:
                row += f"{'░░░':<12} "
            elif len(tools_in_cell) == 1:
                row += f"{'█' + '░░':<12} "
            elif len(tools_in_cell) >= 3:
                row += f"{'███':<12} "
            else:
                row += f"{'██' + '░':<12} "
        lines.append(row)

    lines.append("")
    lines.append("   ░░░ brak    █░░ 1 tool    ██░ 2 tools    ███ 3+")
    lines.append("")

    # Podsumowanie funkcji
    lines.append("Funkcje per narzędzie:")
    for tool_id, tax in sorted(report.taxonomy.items()):
        funcs = []
        funcs.append(tax.function_primary)
        funcs.extend(tax.function_secondary)
        lines.append(f"  {tool_id:<20} → {', '.join(funcs)}")

    return "\n".join(lines)


def format_matched_dims(shared: Dict[str, Any]) -> str:
    """Zwraca tylko wymiary które faktycznie matchują (primary_match)."""
    pm = shared.get("primary_match", {})
    parts = []
    for dim, val in pm.items():
        if val is not None:
            parts.append(f"{dim}={val}")
    sec = shared.get("secondary", {})
    sec_parts = []
    for dim, vals in sec.items():
        if vals:
            sec_parts.append(f"{dim}={','.join(vals)}")
    s = ", ".join(parts)
    if sec_parts:
        s += f" (+sec: {'; '.join(sec_parts)})"
    return s


def render_overlap_matrix(report: HeatMapReport4D) -> str:
    """Macierz nakładania — konkurenci i sąsiedzi."""
    lines: List[str] = []
    lines.append("=== Overlap Matrix (4D) ===")
    lines.append("")

    if not report.overlaps_4d:
        lines.append("Brak nakładań w 4 wymiarach.")
        return "\n".join(lines)

    full = [o for o in report.overlaps_4d if o.severity == "full"]
    partial = [o for o in report.overlaps_4d if o.severity == "partial"]
    complementary = [o for o in report.overlaps_4d if o.severity == "complementary"]

    if full:
        lines.append(f"🔴 Konkurencja ({len(full)} par):")
        for ov in full:
            lines.append(f"  • {' ↔ '.join(ov.tools)}")
            lines.append(f"    {ov.verdict} [{format_matched_dims(ov.shared)}]")
        lines.append("")

    if partial:
        lines.append(f"🟡 Sąsiedztwo ({len(partial)} par):")
        for ov in partial:
            lines.append(f"  • {' ↔ '.join(ov.tools)}")
            lines.append(f"    {ov.verdict} [{format_matched_dims(ov.shared)}]")
        lines.append("")

    if complementary:
        lines.append(
            f"🟢 Komplementarne ({len(complementary)} par) — "
            f"uzyj --json by zobaczyc szczegoly"
        )
        lines.append("")

    if report.overlaps_flat:
        lines.append("--- Nakladania (stary model — po aliasach) ---")
        for ov in report.overlaps_flat:
            lines.append(f"  {ov.domain}: {' ↔ '.join(ov.tools)}")

    return "\n".join(lines)


def render_gaps(report: HeatMapReport4D) -> str:
    """Lista luk w ekosystemie."""
    lines: List[str] = []
    lines.append("=== Gaps (Luki w ekosystemie) ===")
    lines.append("")

    if not report.gaps:
        lines.append("Brak wykrytych luk.")
        return "\n".join(lines)

    crit = [g for g in report.gaps if g.severity == "critical"]
    mod = [g for g in report.gaps if g.severity == "moderate"]
    note = [g for g in report.gaps if g.severity == "notable"]

    if crit:
        lines.append("🔴 Krytyczne:")
        for g in crit:
            lines.append(f"  [{g.layer}/{g.pattern}] {g.description}")

    if mod:
        lines.append("")
        lines.append("🟡 Umiarkowane:")
        for g in mod:
            lines.append(f"  [{g.layer}/{g.pattern}] {g.description}")

    if note:
        lines.append("")
        lines.append("🔵 Warte uwagi:")
        for g in note:
            lines.append(f"  [{g.layer}/{g.pattern}] {g.description}")

    return "\n".join(lines)


def render_summary(report: HeatMapReport4D) -> str:
    """Podsumowanie (domyślny widok) — łączy stare i nowe metryki."""
    lines: List[str] = []
    lines.append("=== Kwatermistrz Heat Map 4D ===")
    lines.append(f"Data: {report.timestamp}")
    lines.append("")

    # Ogólne
    lines.append("Ekosystem:")
    lines.append(f"  Narzędzia: {report.tools_count}")
    p = report.priority_distribution
    lines.append(f"  Priorytety: hot={p['hot']}, warm={p['warm']}, cold={p['cold']}")
    lines.append(f"  Pokrycie domen (stare): {report.coverage_score:.0%}")
    lines.append("")

    # Stack Coverage — skrócona
    lines.append("Stack Coverage (warstwy):")
    for layer_code in LAYERS:
        tools_in_layer = set()
        for d in DOMAINS_4D:
            tools_in_layer.update(report.stack_matrix.get(layer_code, {}).get(d, []))
        count = len(tools_in_layer)
        bar = "█" * min(count, 5) + "░" * max(0, 5 - min(count, 5))
        line = f"  {layer_code} {LAYERS[layer_code]:<20} {bar} {count} narzędzi"
        if count == 0:
            line += " ← GAP"
        lines.append(line)

    lines.append("")

    # Luki (skrócone)
    critical_gaps = [g for g in report.gaps if g.severity == "critical"]
    if critical_gaps:
        lines.append(f"🔴 Krytyczne luki ({len(critical_gaps)}):")
        for g in critical_gaps:
            lines.append(f"  • {g.description}")
        lines.append("")

    # Nakładania
    full_overlaps = [o for o in report.overlaps_4d if o.severity == "full"]
    partial_overlaps = [o for o in report.overlaps_4d if o.severity == "partial"]
    comp_overlaps = [o for o in report.overlaps_4d if o.severity == "complementary"]
    if full_overlaps:
        lines.append(f"🔴 Konkurencja ({len(full_overlaps)} par):")
        for o in full_overlaps:
            lines.append(f"  • {' ↔ '.join(o.tools)}")
        lines.append("")
    if partial_overlaps:
        lines.append(f"🟡 Sąsiedztwo ({len(partial_overlaps)} par)")
        lines.append("")
    if comp_overlaps:
        lines.append(f"🟢 Komplementarne ({len(comp_overlaps)} par)")
        lines.append("")

    # Porty
    if report.port_conflicts:
        lines.append("⚠️  Konflikty portów:")
        for c in report.port_conflicts:
            lines.append(f"  Port {c.port}: {', '.join(c.tools)} ({c.source})")
        lines.append("")

    # Sugestia widoków
    lines.append("---")
    lines.append(
        "Dostepne widoki: --view stack | --view functions | --view overlap | --view gaps"
    )

    return "\n".join(lines)


# ─── Główna logika ───────────────────────────────────────────────────────────────


def build_report(
    tools: List[ToolInfo], taxonomies_raw: Dict[str, Any]
) -> HeatMapReport4D:
    """Zbuduj raport 4D z listy narzędzi i taksonomii."""
    tax = parse_taxonomy(taxonomies_raw)

    # Stare analizy (kompatybilność)
    domains_flat = analyze_domains_flat(tools)
    overlaps_flat = detect_overlaps_flat(tools)
    priorities = analyze_priorities(tools)
    port_conflicts = detect_port_conflicts(tools)

    # Nowe analizy 4D
    stack_matrix = build_stack_matrix(tax)
    function_matrix = build_function_matrix(tax)
    overlaps_4d = detect_overlaps_4d(tax)
    gaps = detect_gaps(stack_matrix, function_matrix)

    # Scores
    total_domains = len(domains_flat)
    coverage_score = sum(1 for d in domains_flat.values() if d.is_well_covered) / max(
        total_domains, 1
    )

    overlapped_tools = sum(len(g.tools) for g in overlaps_flat)
    overlap_score = overlapped_tools / max(len(tools), 1)

    return HeatMapReport4D(
        timestamp=datetime.now().isoformat(),
        tools_count=len(tools),
        priority_distribution=priorities,
        domains_flat=domains_flat,
        overlaps_flat=overlaps_flat,
        port_conflicts=port_conflicts,
        taxonomy=tax,
        stack_matrix=stack_matrix,
        function_matrix=function_matrix,
        overlaps_4d=overlaps_4d,
        gaps=gaps,
        coverage_score=coverage_score,
        overlap_score=overlap_score,
    )


def generate_json_output(report: HeatMapReport4D) -> str:
    """Pełny raport w JSON."""
    gaps_data = []
    for g in report.gaps:
        gaps_data.append(
            {
                "layer": g.layer,
                "function": g.function,
                "domain": g.domain,
                "pattern": g.pattern,
                "severity": g.severity,
                "description": g.description,
            }
        )

    overlaps_data = []
    for o in report.overlaps_4d:
        overlaps_data.append(
            {
                "severity": o.severity,
                "tools": o.tools,
                "shared": o.shared,
                "verdict": o.verdict,
            }
        )

    stack_data = {}
    for lcode in LAYERS:
        stack_data[lcode] = {}
        for dcode in DOMAINS_4D:
            tools_in = report.stack_matrix.get(lcode, {}).get(dcode, [])
            if tools_in:
                stack_data[lcode][dcode] = tools_in

    data = {
        "timestamp": report.timestamp,
        "tools_count": report.tools_count,
        "priority_distribution": report.priority_distribution,
        "coverage_score": report.coverage_score,
        "overlap_score": report.overlap_score,
        "stack_matrix": stack_data,
        "overlaps_4d": overlaps_data,
        "gaps": gaps_data,
        "port_conflicts": [
            {"port": c.port, "tools": c.tools, "source": c.source}
            for c in report.port_conflicts
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kwatermistrz Heat Map 4D — wielowymiarowa mapa ekosystemu narzędzi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Widoki:
  summary     Podsumowanie + kluczowe metryki (domyślny)
  stack       Macierz Layer × Domain — pokrycie warstw
  functions   Macierz Function × Domain — pokrycie funkcji
  overlap     Macierz nakładania 4D
  gaps        Lista luk w ekosystemie

Przykłady:
  python heatmap.py                         # summary
  python heatmap.py --view stack            # Stack Coverage
  python heatmap.py --view gaps             # Luki
  python heatmap.py --view overlap          # Nakładania
  python heatmap.py --json                  # JSON wszystkich danych
  python heatmap.py --output raport.md      # Zapis do pliku
  python heatmap.py --check-ports           # Tylko konflikty portów
        """,
    )

    parser.add_argument(
        "--view",
        type=str,
        default="summary",
        choices=["summary", "stack", "functions", "overlap", "gaps"],
        help="Widok heatmapy (domyślnie: summary)",
    )
    parser.add_argument("--json", action="store_true", help="Wyjście JSON")
    parser.add_argument(
        "--output", "-o", type=str, metavar="PLIK", help="Zapisz do pliku"
    )
    parser.add_argument(
        "--check-ports", action="store_true", help="Tylko konflikty portów"
    )

    args = parser.parse_args()

    # Wczytaj dane
    tools_raw, _ = load_registry()
    if not tools_raw:
        print("Błąd: Rejestr narzędzi jest pusty.", file=sys.stderr)
        sys.exit(1)

    tools = parse_tools(tools_raw)
    taxonomies_raw = load_taxonomy()

    # Tryb tylko porty
    if args.check_ports:
        conflicts = detect_port_conflicts(tools)
        if conflicts:
            print("Wykryte konflikty portów:")
            for c in conflicts:
                print(f"  ⚠️  Port {c.port}: {', '.join(c.tools)} (źródło: {c.source})")
        else:
            print("Brak konfliktów portów.")
        return

    # Zbuduj raport (z danymi 4D jeśli dostępne)
    report = build_report(tools, taxonomies_raw)

    # Generuj wyjście
    if args.json:
        output = generate_json_output(report)
    else:
        view_map = {
            "summary": render_summary,
            "stack": render_stack_coverage,
            "functions": render_function_coverage,
            "overlap": render_overlap_matrix,
            "gaps": render_gaps,
        }
        render_fn = view_map.get(args.view, render_summary)
        output = render_fn(report)

    # Zapis lub stdout
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output, encoding="utf-8")
        print(f"Zapisano raport do: {output_path.absolute()}")
    else:
        print(output)

    # Ostrzeżenie jeśli brak taksonomii
    if not taxonomies_raw:
        print(
            "\n⚠️  UWAGA: Brak danych taksonomii (taxonomy_mapping.json).",
            file=sys.stderr,
        )
        print(
            "   Uruchom klasyfikator lub stwórz taxonomy_mapping.json ręcznie.",
            file=sys.stderr,
        )
        print("   Bez taksonomii widoki 4D będą puste.", file=sys.stderr)


# ── Compat wrappers for mcp_server.py ─────────────────────────────────


def generate_ascii_table(report: HeatMapReport4D) -> str:
    """Alias for render_summary, used by mcp_server.py."""
    return render_summary(report)


def generate_mermaid_diagram(report: HeatMapReport4D) -> str:
    """Generate a Mermaid.js flowchart from the heatmap report.

    Used by mcp_server.py for 'mermaid' output format.
    """
    lines: list[str] = ["graph TD"]
    lines.append(f"  subgraph HeatMap_{report.generated_at}")
    lines.append(f"    direction TB")
    lines.append(f'    title["{report.generated_at}"]')
    for i, (domain, stats) in enumerate(sorted(report.domains.items())):
        node_id = f"D{i}"
        count = stats.tool_count
        label = domain.replace("_", " ").title()
        lines.append(f"    {node_id}[{label}: {count} tools]")
    lines.append("  end")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
