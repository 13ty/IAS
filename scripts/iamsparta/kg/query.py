"""
IAmSparta L1: Knowledge Graph — Query API.

Interfejs zapytań do grafu wiedzy.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from .schema import (
    CapabilityNode,
    Relationship,
    RelationshipType,
    Status,
    ToolNode,
)
from .graph import KnowledgeGraph


class KnowledgeGraphQuery:
    """Query API dla Knowledge Graph."""

    def __init__(self, kg: KnowledgeGraph) -> None:
        self._kg = kg

    # --- Podstawowe zapytania ---

    def find_tool(self, query: str) -> Optional[ToolNode]:
        """Znajdź narzędzie po ID, nazwie lub fragmencie."""
        # Exact match po ID
        tool = self._kg.get_tool(query)
        if tool:
            return tool
        # Fuzzy match po nazwie
        return self._kg.find_tool_by_name(query)

    def list_tools(
        self, domain: Optional[str] = None, status: Optional[str] = None
    ) -> List[ToolNode]:
        """Lista narzędzi z opcjonalnym filtrowaniem."""
        tools = self._kg.all_tools()
        if domain:
            tools = [t for t in tools if t.domain.value == domain]
        if status:
            tools = [t for t in tools if t.status.value == status]
        return tools

    def list_domains(self) -> List[str]:
        """Lista domen w grafie."""
        return [d.id for d in self._kg.all_domains()]

    # --- Relacje ---

    def get_alternatives(self, tool_id: str) -> List[Tuple[ToolNode, str]]:
        """Znajdź alternatywy dla narzędzia."""
        tool = self._kg.get_tool(tool_id)
        if not tool:
            return []
        results = []
        for rel in self._kg.get_relationships(
            source_id=tool_id, rel_type=RelationshipType.ALTERNATIVE
        ):
            target = self._kg.get_tool(rel.target_id)
            if target:
                results.append((target, "alternative"))
        # Dodaj z alternatyw z tool.alternatives
        for alt_name in tool.alternatives:
            alt = self._kg.find_tool_by_name(alt_name)
            if alt and alt.id != tool_id:
                # Sprawdź czy już nie ma relacji
                if not any(r.id == alt.id for r, _ in results):
                    results.append((alt, "listed_alternative"))
        return results

    def get_replacements(self, tool_id: str) -> List[Tuple[ToolNode, str]]:
        """Znajdź co zastąpiło lub zostało zastąpione przez to narzędzie."""
        results = []
        for rel in self._kg.get_relationships(
            source_id=tool_id, rel_type=RelationshipType.REPLACES
        ):
            target = self._kg.get_tool(rel.target_id)
            if target:
                results.append((target, "replaces"))
        for rel in self._kg.get_relationships(
            source_id=tool_id, rel_type=RelationshipType.REPLACED_BY
        ):
            target = self._kg.get_tool(rel.target_id)
            if target:
                results.append((target, "replaced_by"))
        return results

    def get_overlaps(self, tool_id: str) -> List[Tuple[ToolNode, float]]:
        """Znajdź nakładające się narzędzia z wagą."""
        results = []
        for rel in self._kg.get_relationships(
            source_id=tool_id, rel_type=RelationshipType.OVERLAPS_WITH
        ):
            target = self._kg.get_tool(rel.target_id)
            if target:
                results.append((target, rel.weight))
        return results

    def get_complementary(self, tool_id: str) -> List[ToolNode]:
        """Znajdź komplementarne narzędzia."""
        results = []
        for rel in self._kg.get_relationships(
            source_id=tool_id, rel_type=RelationshipType.COMPLEMENTARY
        ):
            target = self._kg.get_tool(rel.target_id)
            if target:
                results.append(target)
        return results

    def get_related(self, tool_id: str) -> List[Tuple[ToolNode, str, float]]:
        """Wszystkie powiązane narzędzia z typem relacji i wagą."""
        results = []
        for rel in self._kg.get_relationships(source_id=tool_id):
            target = self._kg.get_tool(rel.target_id)
            if target:
                results.append((target, rel.rel_type.value, rel.weight))
        # Odwrotne relacje
        for rel in self._kg.get_relationships(target_id=tool_id):
            source = self._kg.get_tool(rel.source_id)
            if source:
                results.append((source, f"inverse_{rel.rel_type.value}", rel.weight))
        return results

    # --- Analiza ---

    def domain_summary(self) -> Dict[str, dict]:
        """Podsumowanie per domena."""
        result = {}
        for domain_id in self._kg._tools_by_domain:
            tools = self._kg.tools_by_domain(domain_id)
            active = sum(1 for t in tools if t.status == Status.ACTIVE)
            result[domain_id] = {
                "count": len(tools),
                "active": active,
                "deprecated": len(tools) - active,
                "tools": [t.id for t in tools],
            }
        return result

    def find_gaps(self) -> List[dict]:
        """Znajdź luki — domeny bez narzędzi o wysokim priorytecie."""
        gaps = []
        for domain_id, tools in self._kg._tools_by_domain.items():
            domain_tools = self._kg.tools_by_domain(domain_id)
            hot_count = sum(1 for t in domain_tools if t.priority.value == "hot")
            if hot_count == 0:
                gaps.append(
                    {
                        "domain": domain_id,
                        "severity": "high",
                        "detail": f"Brak hot-priority tools w domenie {domain_id}",
                        "tool_count": len(domain_tools),
                    }
                )
        return gaps

    def find_orphaned(self) -> List[ToolNode]:
        """Znajdź narzędzia bez żadnych relacji."""
        orphaned = []
        for tool in self._kg.all_tools():
            rels = self._kg.get_relationships(source_id=tool.id)
            if not rels:
                orphaned.append(tool)
        return orphaned

    # --- Ścieżki ---

    def find_path(
        self, from_id: str, to_id: str, max_depth: int = 3
    ) -> Optional[List[Relationship]]:
        """Znajdź ścieżkę między dwoma narzędziami (BFS)."""
        from collections import deque

        visited = {from_id: None}
        queue = deque([from_id])

        while queue and max_depth >= 0:
            current = queue.popleft()
            if current == to_id:
                break
            for rel in self._kg.get_relationships(source_id=current):
                if rel.target_id not in visited:
                    visited[rel.target_id] = (current, rel)
                    queue.append(rel.target_id)

        if to_id not in visited:
            return None

        # Odtwórz ścieżkę
        path = []
        node = to_id
        while node != from_id:
            prev = visited[node]
            if prev is None:
                break
            parent, rel = prev
            path.append(rel)
            node = parent
        path.reverse()
        return path if path else None

    # --- Statystyki ---

    def summary(self) -> dict:
        return self._kg.summary()

    def overlap_analysis(self) -> List[dict]:
        return self._kg.overlap_analysis()

    def full_report(self) -> dict:
        """Pełny raport z podsumowaniem i lukami."""
        return {
            "summary": self.summary(),
            "gaps": self.find_gaps(),
            "domains": self.list_domains(),
            "tools": len(self.list_tools()),
        }
