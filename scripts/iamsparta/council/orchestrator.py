"""
IAmSparta L3: Multi-Agent Council — Orchestrator.

Zarządza cyklem analizy: uruchamia agentów, zbiera opinie, syntezuje rezolucję.
"""

from __future__ import annotations
import sys
from typing import Any, Dict, List, Optional

from .agents import (
    AgentOpinion,
    BaseAgent,
    CouncilResolution,
    SynthesizerAgent,
    create_default_council,
)


class CouncilOrchestrator:
    """
    Orchestrator wieloagentowej rady.

    Przepływ:
    1. Odbiera kontekst (tool_id, goal, porównanie, itp.)
    2. Uruchamia odpowiednich agentów sekwencyjnie
    3. Syntezuje opinie w rezolucję
    """

    def __init__(self, kg: Any = None, ss: Any = None):
        self._kg = kg
        self._ss = ss
        self._agents: Dict[str, BaseAgent] = create_default_council(kg, ss)

    # --- Tryby analizy ---

    def analyze_tool(self, tool_id: str) -> CouncilResolution:
        """Analiza pojedynczego narzędzia."""
        context = {"tool_id": tool_id}
        return self._run([self._agents["analyzer"], self._agents["gap_finder"]])

    def compare_tools(self, tool_a: str, tool_b: str) -> CouncilResolution:
        """Porównanie dwóch narzędzi."""
        context = {"tool_a": tool_a, "tool_b": tool_b}

        opinions: List[AgentOpinion] = []

        # Comparator
        comp = self._agents["comparator"].analyze(context)
        opinions.append(comp)

        # Analyzer dla każdego
        for tid in [tool_a, tool_b]:
            ctx = {"tool_id": tid}
            opinions.append(self._agents["analyzer"].analyze(ctx))

        # Synteza
        synth_opinion = self._synthesize(opinions)
        opinions.append(synth_opinion)

        return self._build_resolution(opinions)

    def strategize(self, goal: str, domain: Optional[str] = None) -> CouncilResolution:
        """Strategia: rekomendacja narzędzi do osiągnięcia celu."""
        context = {"goal": goal, "domain": domain or ""}

        opinions: List[AgentOpinion] = []

        # Strategist
        opinions.append(self._agents["strategist"].analyze(context))

        # Gap finder (opcjonalnie, jeśli domain)
        if domain:
            gap_ctx = {"domain": domain}
            opinions.append(self._agents["gap_finder"].analyze(gap_ctx))

        # Synteza
        synth_opinion = self._synthesize(opinions)
        opinions.append(synth_opinion)

        return self._build_resolution(opinions)

    def full_audit(self) -> CouncilResolution:
        """Pełny audyt ekosystemu narzędzi."""
        opinions: List[AgentOpinion] = []

        # Gap finder
        gap = self._agents["gap_finder"].analyze({"full_audit": True})
        opinions.append(gap)

        # Analyzer dla wszystkich narzędzi (zagregowany)
        if self._kg:
            all_tools = self._kg.all_tools()
            for tool in all_tools[:10]:  # Limit na demo
                opinions.append(self._agents["analyzer"].analyze({"tool_id": tool.id}))

        # Synteza
        synth_opinion = self._synthesize(opinions)
        opinions.append(synth_opinion)

        return self._build_resolution(opinions)

    def custom_run(
        self, agent_names: List[str], context: Dict[str, Any]
    ) -> CouncilResolution:
        """Uruchom wybranych agentów z custom kontekstem."""
        if not agent_names:
            agent_names = list(self._agents.keys())

        available = {k: v for k, v in self._agents.items() if k in agent_names}
        if "synthesizer" not in available and self._agents.get("synthesizer"):
            available["synthesizer"] = self._agents["synthesizer"]

        return self._run(list(available.values()))

    # --- Wewnętrzne ---

    def _run(self, agents: List[BaseAgent]) -> CouncilResolution:
        """Uruchom agentów i zwróć rezolucję."""
        opinions: List[AgentOpinion] = []
        for agent in agents:
            try:
                opinion = agent.analyze({"mode": "auto"})
                opinions.append(opinion)
            except Exception as e:
                opinions.append(
                    AgentOpinion(
                        agent_id=getattr(agent, "agent_id", "unknown"),
                        role=getattr(agent, "role", None),
                        confidence=0.0,
                        findings=[f"Agent error: {e}"],
                    )
                )

        # Dodaj syntezator jeśli nie ma
        if not any(o.agent_id.startswith("synthesizer") for o in opinions):
            synth = self._synthesize(opinions)
            opinions.append(synth)

        return self._build_resolution(opinions)

    def _synthesize(self, opinions: List[AgentOpinion]) -> AgentOpinion:
        """Syntezuje opinie przez SynthesizerAgent."""
        synth = self._agents.get("synthesizer") or SynthesizerAgent(
            knowledge_graph=self._kg, semantic_search=self._ss
        )
        return synth.analyze({"opinions": opinions})

    def _build_resolution(self, opinions: List[AgentOpinion]) -> CouncilResolution:
        """Buduje finalną rezolucję z opinii."""
        if not opinions:
            return CouncilResolution(consensus=False, confidence=0.0)

        # Sprawdź konsensus: jeśli avg confidence > 0.5 → consensus
        avg_conf = sum(o.confidence for o in opinions) / len(opinions)
        consensus = avg_conf > 0.5

        # Majority recommendation (najczęstsza rekomendacja)
        from collections import Counter

        all_recs = [r for o in opinions for r in o.recommendations]
        top_rec = Counter(all_recs).most_common(1)
        majority_rec = top_rec[0][0] if top_rec else ""

        # Dissent (opinie z niską pewnością)
        dissent = [
            f"{o.agent_id} ({o.role.value}): conf={o.confidence:.2f}"
            for o in opinions
            if o.confidence < 0.3
        ]

        return CouncilResolution(
            consensus=consensus,
            confidence=round(avg_conf, 2),
            opinions=opinions,
            majority_recommendation=majority_rec,
            dissent=dissent,
        )


# --- CLI ---


def main():
    import argparse
    from ..kg.graph import KnowledgeGraph
    from ..kg.builder import KnowledgeGraphBuilder

    parser = argparse.ArgumentParser(description="IAmSparta L3: Council")
    parser.add_argument("--tool", type=str, help="Analizuj narzędzie")
    parser.add_argument(
        "--compare", nargs=2, metavar=("A", "B"), help="Porównaj dwa narzędzia"
    )
    parser.add_argument("--goal", type=str, help="Strategia dla celu")
    parser.add_argument("--domain", type=str, help="Filtruj po domenie")
    parser.add_argument("--audit", action="store_true", help="Pełny audyt")
    parser.add_argument(
        "--build", type=str, help="Ścieżka do tool-registry do zbudowania grafu"
    )
    args = parser.parse_args()

    # Build KG jeśli podano źródło
    kg = None
    if args.build:
        builder = KnowledgeGraphBuilder()
        kg = builder.build_from_registry(Path(args.build))
        print(f"📊 KG built: {len(kg.all_tools())} tools")
    else:
        from pathlib import Path

        kg_source = Path(__file__).parent.parent.parent.parent / "tool-registry.yaml"
        if kg_source.exists():
            builder = KnowledgeGraphBuilder()
            kg = builder.build_from_registry(kg_source)

    orchestrator = CouncilOrchestrator(kg=kg)

    if args.tool:
        res = orchestrator.analyze_tool(args.tool)
        print(f"\n{'=' * 60}")
        print(f"🔍 Council Resolution for tool: {args.tool}")
        print(f"{'=' * 60}")
        for op in res.opinions:
            print(f"\n  [{op.role.value}] {op.agent_id}: conf={op.confidence}")
            for f in op.findings:
                print(f"    • {f}")
            for r in op.recommendations:
                print(f"    ⚡ {r}")
        print(f"\n📋 Majority: {res.majority_recommendation}")
        print(f"⚖️  Consensus: {res.consensus} (conf={res.confidence})")

    elif args.compare:
        tool_a, tool_b = args.compare
        res = orchestrator.compare_tools(tool_a, tool_b)
        print(f"\n{'=' * 60}")
        print(f"🔍 Council Comparison: {tool_a} vs {tool_b}")
        print(f"{'=' * 60}")
        for op in res.opinions:
            print(f"\n  [{op.role.value}] {op.agent_id}:")
            for f in op.findings:
                print(f"    • {f}")
            for r in op.recommendations:
                print(f"    ⚡ {r}")
        print(f"\n📋 Verdict: {res.majority_recommendation}")

    elif args.goal:
        res = orchestrator.strategize(args.goal, args.domain)
        print(f"\n{'=' * 60}")
        print(f"🔍 Council Strategy for: {args.goal}")
        print(f"{'=' * 60}")
        for op in res.opinions:
            print(f"\n  [{op.role.value}] {op.agent_id}:")
            for f in op.findings:
                print(f"    • {f}")
            for r in op.recommendations:
                print(f"    ⚡ {r}")

    elif args.audit:
        res = orchestrator.full_audit()
        print(f"\n{'=' * 60}")
        print(f"🔍 Full Ecosystem Audit")
        print(f"{'=' * 60}")
        for op in res.opinions:
            print(f"\n  [{op.role.value}] {op.agent_id}:")
            for f in op.findings:
                print(f"    • {f}")
            for r in op.recommendations:
                print(f"    ⚡ {r}")
        print(f"\n📋 Consensus: {res.consensus} (conf={res.confidence})")

    else:
        parser.print_help()


if __name__ == "__main__":
    from pathlib import Path

    main()
