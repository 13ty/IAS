"""
IAmSparta L3: Multi-Agent Council — Agent Definitions.

Każdy agent specjalizuje się w jednej domenie analizy narzędzi IAS.
Używa L1 Knowledge Graph + L2 Semantic Search do podejmowania decyzji.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentRole(Enum):
    """Role agentów w council."""

    ANALYZER = "analyzer"
    COMPARATOR = "comparator"
    STRATEGIST = "strategist"
    GAP_FINDER = "gap_finder"
    SYNTHESIZER = "synthesizer"


@dataclass
class AgentOpinion:
    """Wynik analizy pojedynczego agenta."""

    agent_id: str
    role: AgentRole
    confidence: float  # 0.0–1.0
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "confidence": self.confidence,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "data": self.data,
        }


@dataclass
class CouncilResolution:
    """Finalna rezolucja council — konsensus lub dissensus."""

    consensus: bool
    confidence: float
    opinions: List[AgentOpinion] = field(default_factory=list)
    majority_recommendation: str = ""
    dissent: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consensus": self.consensus,
            "confidence": self.confidence,
            "opinions": [o.to_dict() for o in self.opinions],
            "majority_recommendation": self.majority_recommendation,
            "dissent": self.dissent,
        }


class BaseAgent:
    """Bazowy agent council."""

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        knowledge_graph: Any = None,
        semantic_search: Any = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.kg = knowledge_graph
        self.ss = semantic_search

    def analyze(self, context: Dict[str, Any]) -> AgentOpinion:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.role.value}/{self.agent_id}"


class AnalyzerAgent(BaseAgent):
    """Agent nr 1: Analizuje pojedyncze narzędzie — jego miejsce w ekosystemie."""

    def __init__(self, agent_id: str = "analyzer-01", **kwargs):
        super().__init__(agent_id, AgentRole.ANALYZER, **kwargs)

    def analyze(self, context: Dict[str, Any]) -> AgentOpinion:
        tool_id = context.get("tool_id", "")
        tool = self.kg.get_tool(tool_id) if self.kg else None

        if not tool:
            return AgentOpinion(
                agent_id=self.agent_id,
                role=self.role,
                confidence=0.0,
                findings=[f"Tool '{tool_id}' not found in KG"],
            )

        findings = []
        recommendations = []

        # Podstawowa analiza
        findings.append(f"Domain: {tool.domain.value}")
        findings.append(f"Priority: {tool.priority.value}")
        findings.append(f"Status: {tool.status.value}")
        findings.append(f"Version: {tool.version}")

        # Analiza statusu
        if tool.is_deprecated():
            replacements = self.kg.find_replacement(tool_id) if self.kg else None
            if replacements:
                rec = f"Replace {tool.name} with {replacements[0].name}"
                recommendations.append(rec)
            else:
                recommendations.append(f"Find replacement for deprecated {tool.name}")

        # Alternatywy
        rels = self.kg.get_relationships(source_id=tool_id) if self.kg else []
        alt_found = any(r.rel_type.value == "alternative" for r in rels)
        if not alt_found:
            recommendations.append(f"Consider finding alternatives for {tool.name}")

        confidence = 0.9 if tool else 0.3
        return AgentOpinion(
            agent_id=self.agent_id,
            role=self.role,
            confidence=confidence,
            findings=findings,
            recommendations=recommendations,
        )


class ComparatorAgent(BaseAgent):
    """Agent nr 2: Porównuje dwa narzędzia — znajdź różnice, overlap, które lepsze."""

    def __init__(self, agent_id: str = "comparator-01", **kwargs):
        super().__init__(agent_id, AgentRole.COMPARATOR, **kwargs)

    def analyze(self, context: Dict[str, Any]) -> AgentOpinion:
        tool_a_id = context.get("tool_a", "")
        tool_b_id = context.get("tool_b", "")

        tool_a = self.kg.get_tool(tool_a_id) if self.kg else None
        tool_b = self.kg.get_tool(tool_b_id) if self.kg else None

        findings = []

        if not tool_a or not tool_b:
            return AgentOpinion(
                agent_id=self.agent_id,
                role=self.role,
                confidence=0.3,
                findings=[f"Cannot compare: tool(s) not found"],
            )

        # Porównanie domen
        if tool_a.domain == tool_b.domain:
            findings.append(f"Same domain: {tool_a.domain.value}")
        else:
            findings.append(
                f"Different domains: {tool_a.domain.value} vs {tool_b.domain.value}"
            )

        # Porównanie priorytetów
        prio_order = {"hot": 3, "warm": 2, "cold": 1}
        diff = prio_order.get(tool_a.priority.value, 0) - prio_order.get(
            tool_b.priority.value, 0
        )
        if diff > 0:
            findings.append(
                f"{tool_a.name} has higher priority ({tool_a.priority.value})"
            )
        elif diff < 0:
            findings.append(
                f"{tool_b.name} has higher priority ({tool_b.priority.value})"
            )
        else:
            findings.append(f"Same priority: {tool_a.priority.value}")

        # Sprawdź alternatywy
        from iamsparta.kg.schema import RelationshipType

        alternatywy = (
            self.kg.get_relationships(
                source_id=tool_a_id, rel_type=RelationshipType.ALTERNATIVE
            )
            if self.kg
            else []
        )
        is_alternative = any(r.target_id == tool_b_id for r in alternatywy)
        if is_alternative:
            findings.append(f"{tool_a.name} and {tool_b.name} are alternatives")

        # Sprawdź overlap
        overlap = (
            self.kg.get_relationships(
                source_id=tool_a_id, rel_type=RelationshipType.OVERLAPS_WITH
            )
            if self.kg
            else []
        )
        is_overlap = any(r.target_id == tool_b_id for r in overlap)
        if is_overlap:
            findings.append(f"{tool_a.name} overlaps with {tool_b.name}")

        recommendations = []
        if tool_a.is_deprecated() and not tool_b.is_deprecated():
            recommendations.append(
                f"Prefer {tool_b.name} over deprecated {tool_a.name}"
            )

        return AgentOpinion(
            agent_id=self.agent_id,
            role=self.role,
            confidence=0.85,
            findings=findings,
            recommendations=recommendations,
        )


class StrategistAgent(BaseAgent):
    """Agent nr 3: Rekomenduje strategię — które narzędzie wybrać i dlaczego."""

    def __init__(self, agent_id: str = "strategist-01", **kwargs):
        super().__init__(agent_id, AgentRole.STRATEGIST, **kwargs)

    def analyze(self, context: Dict[str, Any]) -> AgentOpinion:
        goal = context.get("goal", "")
        domain_filter = context.get("domain", "")

        if not self.kg:
            return AgentOpinion(
                agent_id=self.agent_id,
                role=self.role,
                confidence=0.0,
                findings=["Knowledge Graph not available"],
            )

        findings = []
        recommendations = []

        # Znajdź narzędzia pasujące do celu
        all_tools = self.kg.all_tools()
        candidate_tools = []

        for tool in all_tools:
            if domain_filter and tool.domain.value != domain_filter:
                continue
            if tool.is_deprecated():
                continue
            # Prosta heurystyka: sprawdź czy nazwa lub opis pasuje
            match_score = 0
            goal_lower = goal.lower()
            if goal_lower in tool.name.lower():
                match_score += 10
            if goal_lower in tool.domain.value.lower():
                match_score += 5
            if any(alt.lower() in goal_lower for alt in tool.alternatives):
                match_score += 2
            candidate_tools.append((tool, match_score))

        candidate_tools.sort(key=lambda x: -x[1])
        top_candidates = candidate_tools[:5]

        if not top_candidates:
            findings.append(f"No matching tools found for goal: {goal}")
        else:
            findings.append(f"Found {len(top_candidates)} candidate tools for: {goal}")
            for tool, score in top_candidates:
                findings.append(f"  {tool.name} ({tool.domain.value}) — score: {score}")

        # Rekomendacje
        for tool, _ in top_candidates[:3]:
            recommendations.append(
                f"Consider {tool.name}: {tool.domain.value}, {tool.priority.value} priority"
            )

        return AgentOpinion(
            agent_id=self.agent_id,
            role=self.role,
            confidence=0.7,
            findings=findings,
            recommendations=recommendations,
        )


class GapFinderAgent(BaseAgent):
    """Agent nr 4: Znajduje luki w ekosystemie i sugeruje nowe narzędzia."""

    def __init__(self, agent_id: str = "gapfinder-01", **kwargs):
        super().__init__(agent_id, AgentRole.GAP_FINDER, **kwargs)

    def analyze(self, context: Dict[str, Any]) -> AgentOpinion:
        if not self.kg:
            return AgentOpinion(
                agent_id=self.agent_id,
                role=self.role,
                confidence=0.0,
                findings=["Knowledge Graph not available"],
            )

        findings = []
        recommendations = []

        # 1. Domeny bez hot-priority narzędzi
        hot_tools = self.kg.tools_by_priority("hot")
        hot_domains = set(t.domain.value for t in hot_tools)

        all_tools = self.kg.all_tools()
        all_domains = set(t.domain.value for t in all_tools)

        cold_domains = all_domains - hot_domains
        if cold_domains:
            doms = ", ".join(sorted(cold_domains))
            findings.append(f"Domains without hot-priority: {doms}")
            recommendations.append(
                f"Promote tools in {doms} to hot priority or add new ones"
            )

        # 2. Narzędzia bez alternatyw
        for tool in all_tools:
            if tool.is_deprecated():
                continue
            rels = self.kg.get_relationships(source_id=tool.id)
            has_alt = any(r.rel_type.value == "alternative" for r in rels)
            if not has_alt and not tool.alternatives:
                findings.append(
                    f"No alternatives for: {tool.name} ({tool.domain.value})"
                )

        # 3. Overcrowded domains
        domain_counts: Dict[str, int] = {}
        for t in all_tools:
            domain_counts[t.domain.value] = domain_counts.get(t.domain.value, 0) + 1

        for domain_name, count in domain_counts.items():
            if count > 4:
                findings.append(f"Overcrowded domain: {domain_name} ({count} tools)")
                recommendations.append(f"Consider consolidating {domain_name} tools")

        return AgentOpinion(
            agent_id=self.agent_id,
            role=self.role,
            confidence=0.8,
            findings=findings,
            recommendations=recommendations,
        )


class SynthesizerAgent(BaseAgent):
    """Agent nr 5: Syntezuje opinie pozostałych agentów w finalną rekomendację."""

    def __init__(self, agent_id: str = "synthesizer-01", **kwargs):
        super().__init__(agent_id, AgentRole.SYNTHESIZER, **kwargs)

    def analyze(self, context: Dict[str, Any]) -> AgentOpinion:
        opinions: List[AgentOpinion] = context.get("opinions", [])

        if not opinions:
            return AgentOpinion(
                agent_id=self.agent_id,
                role=self.role,
                confidence=0.0,
                findings=["No opinions to synthesize"],
            )

        findings = []
        recommendations = []

        # Zbierz wszystkie rekomendacje
        all_recs = []
        for op in opinions:
            all_recs.extend(op.recommendations)
            findings.append(
                f"[{op.role.value}/{op.agent_id}] confidence={op.confidence:.2f}, findings={len(op.findings)}"
            )

        # Znajdź najczęściej powtarzające się rekomendacje
        from collections import Counter

        rec_counts = Counter(all_recs)
        top_recs = rec_counts.most_common(3)
        for rec, count in top_recs:
            recommendations.append(f"[consensus {count}/{len(opinions)}] {rec}")

        # Średnia pewność
        avg_conf = (
            sum(o.confidence for o in opinions) / len(opinions) if opinions else 0.0
        )

        return AgentOpinion(
            agent_id=self.agent_id,
            role=self.role,
            confidence=avg_conf,
            findings=findings,
            recommendations=recommendations
            if recommendations
            else ["No clear consensus"],
        )


# Fabryka agentów
def create_default_council(kg: Any = None, ss: Any = None) -> Dict[str, BaseAgent]:
    return {
        "analyzer": AnalyzerAgent(knowledge_graph=kg, semantic_search=ss),
        "comparator": ComparatorAgent(knowledge_graph=kg, semantic_search=ss),
        "strategist": StrategistAgent(knowledge_graph=kg, semantic_search=ss),
        "gap_finder": GapFinderAgent(knowledge_graph=kg, semantic_search=ss),
        "synthesizer": SynthesizerAgent(knowledge_graph=kg, semantic_search=ss),
    }
