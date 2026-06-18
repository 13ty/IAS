"""
IAmSparta L1: Knowledge Graph — Builder.

Parsuje źródła danych (tool_registry.json, tool_inventory.json, .planCS)
i buduje KnowledgeGraph z węzłami i relacjami.
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .schema import (
    CapabilityNode,
    DomainNode,
    KnowledgeGraphState,
    Relationship,
    RelationshipType,
    ToolNode,
    Domain,
    Priority,
    Status,
    ToolType,
)
from .graph import KnowledgeGraph


# --- Ścieżki ---

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TOOL_REGISTRY_PATH = PLUGIN_ROOT / "data" / "tool_registry.json"
PLANCS_PATH = PLUGIN_ROOT / "backend" / ".planCS"
ENVY_PATH = PLUGIN_ROOT / "backend" / ".envy"

TOOL_INVENTORY_PATH = (
    Path(os.environ.get("OPENCODE_CONFIG_DIR", Path.home() / ".config" / "opencode"))
    / "Vaults"
    / "tool-registry"
    / "tool_inventory.json"
)

STATE_FILE = PLUGIN_ROOT / "state" / "iamsparta_kg.json"


# --- Parser .planCS ---


def parse_plancs(path: Path) -> dict:
    """Parsuje .planCS do dict."""
    config = {}
    if not path.exists():
        return config
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            config[key.strip()] = val.strip()
    return config


def parse_envy(path: Path) -> dict:
    """Parsuje .envy do dict."""
    config = {}
    current_section = ""
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


# --- Główny builder ---


def build_graph(
    tool_registry_path: Optional[Path] = None,
    tool_inventory_path: Optional[Path] = None,
    plancs_path: Optional[Path] = None,
    envy_path: Optional[Path] = None,
) -> KnowledgeGraph:
    """Buduje pełny KnowledgeGraph ze wszystkich źródeł."""
    kg = KnowledgeGraph()
    kg._source_files = []
    kg._built_at = datetime.now().isoformat()

    tr_path = tool_registry_path or TOOL_REGISTRY_PATH
    ti_path = tool_inventory_path or TOOL_INVENTORY_PATH
    pc_path = plancs_path or PLANCS_PATH
    ev_path = envy_path or ENVY_PATH

    # --- 1. Domeny ---
    for d in Domain:
        kg.add_domain(
            DomainNode(id=d.value, name=d.value, description=f"Domain: {d.value}")
        )

    # --- 2. Tool Registry (główne źródło) ---
    if tr_path.exists():
        kg._source_files.append(str(tr_path))
        data = json.loads(tr_path.read_text(encoding="utf-8"))
        _parse_tool_registry(kg, data)

    # --- 3. Tool Inventory (uzupełnienie — archiwum, alternatywy, use_count) ---
    if ti_path.exists():
        kg._source_files.append(str(ti_path))
        data = json.loads(ti_path.read_text(encoding="utf-8"))
        _parse_tool_inventory(kg, data)

    # --- 4. .planCS (konfiguracja katalogów) ---
    if pc_path.exists():
        kg._source_files.append(str(pc_path))
        plancs = parse_plancs(pc_path)
        _add_plancs_metadata(kg, plancs)

    # --- 5. .envy (porty, zależności zewnętrzne) ---
    if ev_path.exists():
        kg._source_files.append(str(ev_path))
        envy = parse_envy(ev_path)
        _add_envy_metadata(kg, envy)

    # --- 6. Automatyczne relacje ---
    _build_automatic_relationships(kg)

    return kg


def _parse_tool_registry(kg: KnowledgeGraph, data: dict) -> None:
    """Parsuje tool_registry.json."""
    tools = data.get("tools", {})
    for tool_id, tool_data in tools.items():
        node = ToolNode(
            id=tool_id,
            name=tool_data.get("name", tool_id),
            version=str(tool_data.get("version", "0.0.0")),
            tool_type=ToolType(tool_data.get("type", "cli")),
            domain=Domain.from_str(tool_data.get("domain", "other")),
            priority=Priority(tool_data.get("priority", "warm")),
            status=Status(tool_data.get("status", "active")),
            description=tool_data.get("description", ""),
            location=tool_data.get("location", ""),
            run_command=tool_data.get("run_command", ""),
            update_command=tool_data.get("update_command", ""),
            alternatives=tool_data.get("alternatives", []),
        )
        kg.add_tool(node)


def _parse_tool_inventory(kg: KnowledgeGraph, data: dict) -> None:
    """Parsuje tool_inventory.json — uzupełnia brakujące narzędzia i archiwum."""
    tools = data.get("tools", {})
    for path_key, tool_data in tools.items():
        name = tool_data.get("name", "")
        if not name:
            continue

        # Znajdź po nazwie lub dodaj jako nowe
        existing = kg.find_tool_by_name(name)
        if existing:
            # Uzupełnij metadane z inventory
            if tool_data.get("analysis"):
                existing.metadata["analysis"] = tool_data["analysis"]
            if tool_data.get("use_count", 0) > 0:
                existing.metadata["use_count"] = tool_data["use_count"]
            continue

        # Dodaj nowe narzędzie z inventory (jeśli nie istnieje w registry)
        domain_str = tool_data.get("domain", "other")
        node = ToolNode(
            id=name.replace(" ", "-").replace("/", "-"),
            name=name,
            version=str(tool_data.get("version", "0.0.0")),
            tool_type=ToolType(tool_data.get("type", "unknown")),
            domain=Domain.from_str(domain_str),
            priority=Priority(tool_data.get("priority", "cold")),
            status=Status(tool_data.get("status", "trial")),
            description=tool_data.get("description", ""),
            run_command=tool_data.get("run_command", ""),
            location=path_key,
            alternatives=tool_data.get("alternatives") or [],
            metadata={
                "source": "tool_inventory",
                "use_count": tool_data.get("use_count", 0),
            },
        )
        kg.add_tool(node)

    # Archiwum (deprecated tools)
    archive = data.get("archive", {})
    for path_key, tool_data in archive.items():
        name = tool_data.get("name", "")
        if not name:
            continue
        existing = kg.find_tool_by_name(name)
        if existing:
            existing.status = Status.DEPRECATED
            existing.arch_deprecated_at = tool_data.get("deprecated_at", "")
            existing.arch_deprecation_reason = tool_data.get("deprecation_reason", "")
            if tool_data.get("replaced_by"):
                # Dodaj relację replaced_by
                rel = Relationship(
                    source_id=existing.id,
                    target_id=tool_data["replaced_by"],
                    rel_type=RelationshipType.REPLACED_BY,
                    metadata={"reason": tool_data.get("deprecation_reason", "")},
                )
                kg.add_relationship(rel)
                # Odwrotna relacja replaces
                replaces_rel = Relationship(
                    source_id=tool_data["replaced_by"],
                    target_id=existing.id,
                    rel_type=RelationshipType.REPLACES,
                )
                kg.add_relationship(replaces_rel)


def _add_plancs_metadata(kg: KnowledgeGraph, plancs: dict) -> None:
    """Dodaje metadane z .planCS do grafu."""
    # .planCS może zawierać info o katalogach — dodajemy jako metadata do grafu
    kg._source_files.append("plancs")


def _add_envy_metadata(kg: KnowledgeGraph, envy: dict) -> None:
    """Dodaje metadane z .envy do grafu."""
    ext = envy.get("external_dependencies", {})
    used_ports = []
    for key, val in ext.items():
        if "port" in key.lower():
            try:
                used_ports.append(int(val))
            except ValueError:
                pass

    # Dodaj porty jako metadata do narzędzi które ich używają
    for tool_id in used_ports:
        tool = kg.get_tool(f"port-{tool_id}")
        if tool:
            tool.metadata["port"] = tool_id


def _build_automatic_relationships(kg: KnowledgeGraph) -> None:
    """Automatyczne wnioskowanie relacji między narzędziami."""
    # 1. alternatywy → ALTERNATIVE + OVERLAPS_WITH
    for tool in kg.all_tools():
        for alt_name in tool.alternatives:
            alt_tool = kg.find_tool_by_name(alt_name)
            if alt_tool:
                # Skierowana: tool → alt = alternative
                rel = Relationship(
                    source_id=tool.id,
                    target_id=alt_tool.id,
                    rel_type=RelationshipType.ALTERNATIVE,
                )
                kg.add_relationship(rel)
                # Wzajemne nakładanie
                overlap = Relationship(
                    source_id=tool.id,
                    target_id=alt_tool.id,
                    rel_type=RelationshipType.OVERLAPS_WITH,
                    weight=0.7,
                )
                kg.add_relationship(overlap)

    # 2. Narzędzia w tej samej domenie → OVERLAPS_WITH (słabsze)
    domain_tools: Dict[str, List[str]] = {}
    for tool in kg.all_tools():
        domain_tools.setdefault(tool.domain.value, []).append(tool.id)

    for domain, tool_ids in domain_tools.items():
        for i in range(len(tool_ids)):
            for j in range(i + 1, len(tool_ids)):
                if tool_ids[i] != tool_ids[j]:
                    # Sprawdź czy już istnieje relacja między tymi narzędziami
                    existing = kg.get_relationships(
                        source_id=tool_ids[i], target_id=tool_ids[j]
                    )
                    if not existing:
                        rel = Relationship(
                            source_id=tool_ids[i],
                            target_id=tool_ids[j],
                            rel_type=RelationshipType.COMPLEMENTARY,
                            weight=0.3,
                            metadata={"domain": domain},
                        )
                        kg.add_relationship(rel)

    # 3. Narzędzia o statusie deprecated → REPLACED_BY (jeśli mają alternatywę)
    for tool in kg.all_tools():
        if tool.status == Status.DEPRECATED and tool.alternatives:
            for alt_name in tool.alternatives:
                alt_tool = kg.find_tool_by_name(alt_name)
                if alt_tool:
                    rel = Relationship(
                        source_id=tool.id,
                        target_id=alt_tool.id,
                        rel_type=RelationshipType.REPLACED_BY,
                        weight=0.9,
                        metadata={
                            "reason": tool.arch_deprecation_reason or "deprecated"
                        },
                    )
                    kg.add_relationship(rel)


# --- Zapis / odczyt stanu ---


def save_graph(kg: KnowledgeGraph, path: Optional[Path] = None) -> None:
    """Serializuje graf do JSON i zapisuje."""
    save_path = path or STATE_FILE
    save_path.parent.mkdir(parents=True, exist_ok=True)

    state = kg.to_state()
    data = {
        "nodes": state.nodes,
        "relationships": [
            {
                "source_id": r.source_id,
                "target_id": r.target_id,
                "rel_type": r.rel_type.value,
                "weight": r.weight,
                "metadata": r.metadata,
            }
            for r in state.relationships
        ],
        "built_at": state.built_at,
        "source_files": state.source_files,
    }
    save_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_graph(path: Optional[Path] = None) -> Optional[KnowledgeGraph]:
    """Wczytuje graf z JSON."""
    load_path = path or STATE_FILE
    if not load_path.exists():
        return None

    data = json.loads(load_path.read_text(encoding="utf-8"))
    kg = KnowledgeGraph()

    # Wczytaj węzły
    for node_id, node_data in data.get("nodes", {}).items():
        kind = node_data.get("_kind", "")
        if kind == "tool":
            kg.add_tool(
                ToolNode(
                    id=node_id,
                    name=node_data.get("name", node_id),
                    version=node_data.get("version", "0.0.0"),
                    tool_type=ToolType(node_data.get("tool_type", "cli")),
                    domain=Domain.from_str(node_data.get("domain", "other")),
                    priority=Priority(node_data.get("priority", "warm")),
                    status=Status(node_data.get("status", "active")),
                    description=node_data.get("description", ""),
                    location=node_data.get("location"),
                    run_command=node_data.get("run_command"),
                    update_command=node_data.get("update_command"),
                    alternatives=node_data.get("alternatives", []),
                    tags=node_data.get("tags", []),
                    metadata=node_data.get("metadata", {}),
                )
            )
        elif kind == "capability":
            kg.add_capability(
                CapabilityNode(**{k: v for k, v in node_data.items() if k != "_kind"})
            )
        elif kind == "domain":
            kg.add_domain(
                DomainNode(**{k: v for k, v in node_data.items() if k != "_kind"})
            )

    # Wczytaj relacje
    for rel_data in data.get("relationships", []):
        try:
            rel = Relationship(
                source_id=rel_data["source_id"],
                target_id=rel_data["target_id"],
                rel_type=RelationshipType(rel_data["rel_type"]),
                weight=rel_data.get("weight", 1.0),
                metadata=rel_data.get("metadata", {}),
            )
            kg.add_relationship(rel)
        except (KeyError, ValueError):
            continue

    kg._built_at = data.get("built_at", "")
    kg._source_files = data.get("source_files", [])
    return kg


# --- CLI ---


class KnowledgeGraphBuilder:
    """Builder dla Knowledge Graph — wrapper wokół build_graph()."""

    def __init__(self, registry_path: Optional[Path] = None):
        self._registry_path = registry_path

    def build_from_registry(
        self, registry_path: Optional[Path] = None
    ) -> KnowledgeGraph:
        """Build graph from tool registry."""
        path = registry_path or self._registry_path
        return build_graph(tool_registry_path=path)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="IAmSparta L1: Knowledge Graph Builder"
    )
    parser.add_argument("--build", action="store_true", help="Zbuduj graf od nowa")
    parser.add_argument("--load", action="store_true", help="Wczytaj zapisany graf")
    parser.add_argument("--summary", action="store_true", help="Pokaż podsumowanie")
    parser.add_argument("--save", action="store_true", help="Zapisz graf do pliku")
    parser.add_argument("--output", type=str, help="Ścieżka outputu (JSON)")
    args = parser.parse_args()

    if args.build:
        print("🏗️  Budowanie Knowledge Graph...")
        kg = build_graph()
        print(f"   ✅ Narzędzia: {kg.tool_count()}")
        print(f"   ✅ Domeny: {len(kg.all_domains())}")
        print(f"   ✅ Relacje: {len(kg._relationships)}")
        if args.save:
            save_graph(kg)
            print(f"   ✅ Zapisano do: {STATE_FILE}")
        if args.output:
            Path(args.output).write_text(
                json.dumps(kg.summary(), indent=2), encoding="utf-8"
            )
            print(f"   ✅ Podsumowanie zapisane: {args.output}")

    elif args.load:
        kg = load_graph()
        if kg:
            print(f"📂 Wczytano graf ({kg.tool_count()} narzędzi)")
        else:
            print("❌ Brak zapisanego grafu")

    elif args.summary:
        kg = load_graph()
        if kg:
            print(json.dumps(kg.summary(), indent=2))
        else:
            print("❌ Brak grafu — użyj --build najpierw")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
