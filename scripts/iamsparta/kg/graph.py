"""
IAmSparta L1: Knowledge Graph — In-Memory Graph Engine.

Zarządza węzłami i krawędziami w pamięci, zapewnia szybki dostęp.
Używa: dict dla O(1) lookup nodes, list dla edges, defaultdict dla indeksów.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .schema import (
    CapabilityNode,
    DomainNode,
    KnowledgeGraphState,
    Relationship,
    RelationshipType,
    Status,
    ToolNode,
)


class KnowledgeGraph:
    """Główny graf wiedzy — węzły + krawędzie + indeksy."""

    def __init__(self) -> None:
        # Węzły
        self._tools: Dict[str, ToolNode] = {}
        self._capabilities: Dict[str, CapabilityNode] = {}
        self._domains: Dict[str, DomainNode] = {}

        # Krawędzie
        self._relationships: List[Relationship] = []

        # Indeksy dla szybkich zapytań
        self._rels_by_source: Dict[str, List[Relationship]] = defaultdict(list)
        self._rels_by_target: Dict[str, List[Relationship]] = defaultdict(list)
        self._rels_by_type: Dict[RelationshipType, List[Relationship]] = defaultdict(
            list
        )
        self._tools_by_domain: Dict[str, List[str]] = defaultdict(list)
        self._tools_by_priority: Dict[str, List[str]] = defaultdict(list)
        self._tools_by_status: Dict[str, List[str]] = defaultdict(list)
        self._tools_by_type: Dict[str, List[str]] = defaultdict(list)

        # Metadane
        self._built_at: str = ""
        self._source_files: List[str] = []

    # --- Zarządzanie węzłami ---

    def add_tool(self, tool: ToolNode) -> None:
        self._tools[tool.id] = tool
        self._tools_by_domain[tool.domain.value].append(tool.id)
        self._tools_by_priority[tool.priority.value].append(tool.id)
        self._tools_by_status[tool.status.value].append(tool.id)
        self._tools_by_type[tool.tool_type.value].append(tool.id)

    def add_capability(self, cap: CapabilityNode) -> None:
        self._capabilities[cap.id] = cap

    def add_domain(self, domain: DomainNode) -> None:
        self._domains[domain.id] = domain

    def get_tool(self, tool_id: str) -> Optional[ToolNode]:
        return self._tools.get(tool_id)

    def get_capability(self, cap_id: str) -> Optional[CapabilityNode]:
        return self._capabilities.get(cap_id)

    def get_domain(self, domain_id: str) -> Optional[DomainNode]:
        return self._domains.get(domain_id)

    def all_tools(self) -> List[ToolNode]:
        return list(self._tools.values())

    def all_capabilities(self) -> List[CapabilityNode]:
        return list(self._capabilities.values())

    def all_domains(self) -> List[DomainNode]:
        return list(self._domains.values())

    def tool_count(self) -> int:
        return len(self._tools)

    def capability_count(self) -> int:
        return len(self._capabilities)

    # --- Zarządzanie krawędziami ---

    def add_relationship(self, rel: Relationship) -> None:
        self._relationships.append(rel)
        self._rels_by_source[rel.source_id].append(rel)
        self._rels_by_target[rel.target_id].append(rel)
        self._rels_by_type[rel.rel_type].append(rel)

    def add_relationships(self, rels: List[Relationship]) -> None:
        for r in rels:
            self.add_relationship(r)

    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        rel_type: Optional[RelationshipType] = None,
    ) -> List[Relationship]:
        """Filtruj relacje według źródła, celu i/lub typu (AND)."""
        results: List[Relationship] = list(self._relationships)

        if source_id:
            results = [r for r in results if r.source_id == source_id]
        if target_id:
            results = [r for r in results if r.target_id == target_id]
        if rel_type:
            results = [r for r in results if r.rel_type == rel_type]

        return results

    # --- Indeksy ---

    def tools_by_domain(self, domain: str) -> List[ToolNode]:
        return [
            self._tools[i]
            for i in self._tools_by_domain.get(domain, [])
            if i in self._tools
        ]

    def tools_by_priority(self, priority: str) -> List[ToolNode]:
        return [
            self._tools[i]
            for i in self._tools_by_priority.get(priority, [])
            if i in self._tools
        ]

    def tools_by_status(self, status: str) -> List[ToolNode]:
        return [
            self._tools[i]
            for i in self._tools_by_status.get(status, [])
            if i in self._tools
        ]

    def tools_by_type(self, tool_type: str) -> List[ToolNode]:
        return [
            self._tools[i]
            for i in self._tools_by_type.get(tool_type, [])
            if i in self._tools
        ]

    # --- Statystyki ---

    def summary(self) -> dict:
        """Zwraca podsumowanie grafu."""
        domains = {}
        for d, ids in self._tools_by_domain.items():
            domains[d] = len(ids)

        types = {}
        for t, ids in self._tools_by_type.items():
            types[t] = len(ids)

        return {
            "tools": self.tool_count(),
            "capabilities": self.capability_count(),
            "domains": len(self._domains),
            "relationships": len(self._relationships),
            "by_domain": dict(domains),
            "by_type": dict(types),
            "source_files": self._source_files,
            "built_at": self._built_at,
        }

    def domain_coverage_heatmap(self) -> dict:
        """Macierz: domena × priorytet."""
        matrix = {}
        for domain_name in self._tools_by_domain:
            tools = self.tools_by_domain(domain_name)
            counts = {"hot": 0, "warm": 0, "cold": 0}
            for t in tools:
                if t.priority.value in counts:
                    counts[t.priority.value] += 1
            matrix[domain_name] = counts
        return matrix

    def overlap_analysis(self) -> List[dict]:
        """Znajdź narzędzia które mają alternatywy w tym samym zbiorze."""
        overlaps = []
        for tool_id, tool in self._tools.items():
            if tool.alternatives:
                present_alts = [
                    alt for alt in tool.alternatives if self.find_tool_by_name(alt)
                ]
                if present_alts:
                    overlaps.append(
                        {
                            "tool": tool_id,
                            "alternatives_in_registry": present_alts,
                        }
                    )
        return overlaps

    def find_tool_by_name(self, name: str) -> Optional[ToolNode]:
        """Znajdź narzędzie po nazwie (fuzzy match)."""
        name_lower = name.lower()
        for t in self._tools.values():
            if name_lower in t.name.lower() or name_lower in t.id.lower():
                return t
        return None

    def find_replacement(self, tool_id: str) -> List[ToolNode]:
        """Znajdź zamienniki dla zdeprecjonowanego narzędzia."""
        tool = self._tools.get(tool_id)
        if not tool or tool.status != Status.DEPRECATED:
            return []

        replacements = []
        for rel in self._rels_by_source.get(tool_id, []):
            if rel.rel_type == RelationshipType.REPLACED_BY:
                replacement = self._tools.get(rel.target_id)
                if replacement:
                    replacements.append(replacement)
        return replacements

    # --- Serializacja ---

    def to_state(self) -> KnowledgeGraphState:
        return KnowledgeGraphState(
            nodes={
                **_tools_dict_to_serializable(self._tools),
                **_caps_dict_to_serializable(self._capabilities),
                **_domains_dict_to_serializable(self._domains),
            },
            relationships=self._relationships,
            built_at=self._built_at,
            source_files=self._source_files,
        )

    @classmethod
    def from_state(cls, state: KnowledgeGraphState) -> KnowledgeGraph:
        kg = cls()
        kg._built_at = state.built_at
        kg._source_files = state.source_files
        for node_dict in state.nodes.values():
            kind = node_dict.get("_kind", "")
            if kind == "tool":
                kg.add_tool(
                    ToolNode(**{k: v for k, v in node_dict.items() if k != "_kind"})
                )
            elif kind == "capability":
                kg.add_capability(
                    CapabilityNode(
                        **{k: v for k, v in node_dict.items() if k != "_kind"}
                    )
                )
            elif kind == "domain":
                kg.add_domain(
                    DomainNode(**{k: v for k, v in node_dict.items() if k != "_kind"})
                )
        kg.add_relationships(state.relationships)
        return kg

    def __repr__(self) -> str:
        return f"KnowledgeGraph(tools={self.tool_count()}, rels={len(self._relationships)})"


# --- Serializacja helpery ---


def _tools_dict_to_serializable(tools: dict) -> dict:
    return {
        tid: {
            "_kind": "tool",
            **tool.__dict__,
            "domain": tool.domain.value,
            "priority": tool.priority.value,
            "status": tool.status.value,
            "tool_type": tool.tool_type.value,
        }
        for tid, tool in tools.items()
    }


def _caps_dict_to_serializable(caps: dict) -> dict:
    return {cid: {"_kind": "capability", **cap.__dict__} for cid, cap in caps.items()}


def _domains_dict_to_serializable(domains: dict) -> dict:
    return {did: {"_kind": "domain", **d.__dict__} for did, d in domains.items()}
