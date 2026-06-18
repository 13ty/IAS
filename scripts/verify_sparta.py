#!/usr/bin/env python3
"""Weryfikacja SPARTY: sprawdza importy i podstawową funkcjonalność L1-L3."""

import sys
from pathlib import Path

scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))


def check(label, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {label} {detail}")
    return condition


def main():
    print("=" * 60)
    print("IAmSparta — Weryfikacja L1-L3")
    print("=" * 60)

    all_ok = True

    # L1: Schema
    print("\n📦 L1: Schema")
    try:
        from iamsparta.kg.schema import (
            ToolNode,
            DomainNode,
            CapabilityNode,
            Relationship,
            RelationshipType,
            Status,
            Priority,
            Domain,
            ToolType,
        )

        all_ok &= check("Import schema", True)

        # Create instances
        tool = ToolNode(
            id="test-01",
            name="Test Tool",
            tool_type=ToolType.CLI,
            domain=Domain.TESTING,
            priority=Priority.HOT,
            status=Status.ACTIVE,
            version="1.0.0",
            description="A test tool",
        )
        tool2 = ToolNode(
            id="test-02",
            name="Test Tool 2",
            tool_type=ToolType.PLUGIN,
            domain=Domain.TESTING,
            priority=Priority.WARM,
            status=Status.ACTIVE,
            version="1.0.0",
            description="Second test tool",
        )
        all_ok &= check("ToolNode creation", tool.id == "test-01" and tool.is_active())
        all_ok &= check("ToolNode serialization", isinstance(tool.to_dict(), dict))
        all_ok &= check("ToolNode deprecated check", not tool.is_deprecated())

        dep_tool = ToolNode(
            id="dep-01",
            name="Deprecated Tool",
            tool_type=ToolType.CLI,
            domain=Domain.TESTING,
            priority=Priority.COLD,
            status=Status.DEPRECATED,
            version="0.5.0",
            description="Old deprecated tool",
        )
        all_ok &= check(
            "ToolNode deprecated status",
            dep_tool.is_deprecated() and not dep_tool.is_active(),
        )

        dom = DomainNode(id="testing", name="Testing Tools")
        all_ok &= check("DomainNode creation", dom.id == "testing")

        cap = CapabilityNode(
            id="cap-01",
            name="Render",
            description="Renders diagrams",
            category="rendering",
        )
        all_ok &= check("CapabilityNode creation", cap.id == "cap-01")

        rel = Relationship(
            source_id="test-01",
            target_id="test-02",
            rel_type=RelationshipType.ALTERNATIVE,
            weight=0.85,
        )
        all_ok &= check("Relationship creation", rel.weight == 0.85)
        all_ok &= check("Relationship reverse", rel.reverse().source_id == "test-02")

        # Enum values
        all_ok &= check(
            "Domain enums",
            all(d in [e.value for e in Domain] for d in ["testing", "dev", "ai"]),
        )
        all_ok &= check(
            "Priority enums",
            all(p in [e.value for e in Priority] for p in ["hot", "warm", "cold"]),
        )
        all_ok &= check(
            "Status enums",
            all(s in [e.value for e in Status] for s in ["active", "deprecated"]),
        )
        all_ok &= check(
            "RelationshipType enums",
            all(
                r in [e.value for e in RelationshipType]
                for r in [
                    "alternative",
                    "depends_on",
                    "overlaps_with",
                    "complementary",
                    "replaced_by",
                    "replaces",
                ]
            ),
        )

    except Exception as e:
        all_ok &= check(f"Schema import failed: {e}", False)
        print(f"    ❌ {e}")

    # L1: Knowledge Graph
    print("\n📊 L1: Knowledge Graph")
    try:
        from iamsparta.kg.graph import KnowledgeGraph

        kg = KnowledgeGraph()
        all_ok &= check("KG creation", True)

        # Add domains
        kg.add_domain(DomainNode(id="testing", name="Testing"))
        kg.add_domain(DomainNode(id="dev", name="Development"))
        all_ok &= check("KG add domains", len(kg.all_domains()) == 2)

        # Add tools
        t1 = ToolNode(
            id="t1",
            name="Puppeteer",
            tool_type=ToolType.PLUGIN,
            domain=Domain.TESTING,
            priority=Priority.HOT,
            status=Status.ACTIVE,
            version="2.0.0",
            description="Browser automation tool",
            alternatives=["Playwright"],
        )
        t2 = ToolNode(
            id="t2",
            name="Playwright",
            tool_type=ToolType.PLUGIN,
            domain=Domain.TESTING,
            priority=Priority.HOT,
            status=Status.ACTIVE,
            version="3.0.0",
            description="Cross-browser automation",
        )
        t3 = ToolNode(
            id="t3",
            name="Old Tool",
            tool_type=ToolType.CLI,
            domain=Domain.DEV,
            priority=Priority.COLD,
            status=Status.DEPRECATED,
            version="0.1.0",
            description="Legacy tool",
        )
        kg.add_tool(t1)
        kg.add_tool(t2)
        kg.add_tool(t3)
        all_ok &= check("KG add tools", len(kg.all_tools()) == 3)

        # Relationships
        kg.add_relationship(Relationship("t1", "t2", RelationshipType.ALTERNATIVE, 0.9))
        kg.add_relationship(Relationship("t3", "t1", RelationshipType.REPLACED_BY, 0.7))
        all_ok &= check(
            "KG add relationships", len(kg.get_relationships(source_id="t1")) == 1
        )

        # Queries
        all_ok &= check("KG get_tool", kg.get_tool("t1").name == "Puppeteer")
        all_ok &= check(
            "KG find_tool_by_name", kg.find_tool_by_name("Playwright").id == "t2"
        )
        all_ok &= check("KG tools_by_domain", len(kg.tools_by_domain("testing")) == 2)
        all_ok &= check("KG tools_by_priority", len(kg.tools_by_priority("hot")) == 2)
        all_ok &= check("KG tools_by_status", len(kg.tools_by_status("active")) == 2)
        all_ok &= check("KG find_replacement", kg.find_replacement("t3")[0].id == "t1")

        # Summary
        s = kg.summary()
        all_ok &= check("KG summary tools", s["tools"] == 3)
        all_ok &= check("KG summary domains", s["domains"] == 2)
        all_ok &= check("KG summary by_domain", "testing" in s["by_domain"])

        # Overlap analysis
        overlap = kg.overlap_analysis()
        all_ok &= check("KG overlap_analysis", len(overlap) > 0)

    except Exception as e:
        all_ok &= check(f"Knowledge Graph failed: {e}", False)
        import traceback

        traceback.print_exc()

    # L1: Query API
    print("\n🔍 L1: Query API")
    try:
        from iamsparta.kg.query import KnowledgeGraphQuery

        q = KnowledgeGraphQuery(kg)

        all_ok &= check("Query find_tool by id", q.find_tool("t1") is not None)
        all_ok &= check("Query find_tool by name", q.find_tool("Puppeteer") is not None)
        all_ok &= check("Query find_tool not found", q.find_tool("nonexistent") is None)
        all_ok &= check("Query list_tools", len(q.list_tools()) == 3)
        all_ok &= check(
            "Query list_tools filter domain", len(q.list_tools(domain="testing")) == 2
        )
        all_ok &= check("Query list_domains", len(q.list_domains()) == 2)
        all_ok &= check("Query get_alternatives", len(q.get_alternatives("t1")) > 0)

        alt_names = [t.name for t, _ in q.get_alternatives("t1")]
        all_ok &= check("Query alternatives correct", "Playwright" in alt_names)

        all_ok &= check("Query get_replacements", len(q.get_replacements("t3")) > 0)
        all_ok &= check("Query find_path", q.find_path("t3", "t2") is not None)

        gaps = q.find_gaps()
        all_ok &= check("Query find_gaps", isinstance(gaps, list))

        s = q.summary()
        all_ok &= check("Query summary", s["tools"] == 3)

        report = q.full_report()
        all_ok &= check("Query full_report", "summary" in report and "gaps" in report)

    except Exception as e:
        all_ok &= check(f"Query API failed: {e}", False)
        import traceback

        traceback.print_exc()

    # L1: Builder
    print("\n🏗️  L1: Builder")
    try:
        from iamsparta.kg.builder import KnowledgeGraphBuilder

        builder = KnowledgeGraphBuilder()
        all_ok &= check("Builder creation", True)
        # Can't test full build without tool-registry.yaml, but import works
    except Exception as e:
        all_ok &= check(f"Builder import failed: {e}", False)

    # L2: Semantic Layer
    print("\n🧠 L2: Semantic Layer")
    try:
        from iamsparta.semantic.embeddings import (
            generate_embedding,
            get_lmstudio_config,
            generate_capability_embedding,
        )
        from iamsparta.semantic.search import SemanticSearch

        all_ok &= check("Semantic Layer imports", True)

        ss = SemanticSearch()
        all_ok &= check("SemanticSearch creation", True)

    except Exception as e:
        all_ok &= check(f"Semantic Layer imports failed: {e}", False)
        # Expected if LMStudio/LanceDB not running

    # L3: Multi-Agent Council
    print("\n🏛️  L3: Multi-Agent Council")
    try:
        from iamsparta.council.agents import (
            AnalyzerAgent,
            ComparatorAgent,
            StrategistAgent,
            GapFinderAgent,
            SynthesizerAgent,
            create_default_council,
            AgentOpinion,
            CouncilResolution,
        )

        all_ok &= check("Council agents imports", True)

        # Agent creation
        agent = AnalyzerAgent(agent_id="test-analyzer", knowledge_graph=kg)
        all_ok &= check("AnalyzerAgent creation", agent.agent_id == "test-analyzer")

        # Agent analysis
        opinion = agent.analyze({"tool_id": "t1"})
        all_ok &= check("AnalyzerAgent analysis", opinion.confidence > 0.5)
        all_ok &= check("AnalyzerAgent findings", len(opinion.findings) > 0)

        # Comparator
        comp = ComparatorAgent(knowledge_graph=kg)
        comp_opinion = comp.analyze({"tool_a": "t1", "tool_b": "t2"})
        all_ok &= check("ComparatorAgent analysis", comp_opinion.confidence > 0.5)
        all_ok &= check(
            "Comparator finds alternatives",
            any("alternative" in f for f in comp_opinion.findings),
        )

        # Strategist
        strat = StrategistAgent(knowledge_graph=kg)
        strat_opinion = strat.analyze({"goal": "browser testing", "domain": "testing"})
        all_ok &= check("StrategistAgent analysis", strat_opinion.confidence > 0.5)

        # Gap Finder
        gf = GapFinderAgent(knowledge_graph=kg)
        gf_opinion = gf.analyze({"full_audit": True})
        all_ok &= check("GapFinderAgent analysis", len(gf_opinion.findings) > 0)
        all_ok &= check(
            "GapFinderAgent recommendations", len(gf_opinion.recommendations) > 0
        )

        # Synthesizer
        synth = SynthesizerAgent(knowledge_graph=kg)
        synth_opinion = synth.analyze({"opinions": [opinion, comp_opinion]})
        all_ok &= check("SynthesizerAgent analysis", synth_opinion.confidence > 0)

        # Council Resolution
        res = CouncilResolution(consensus=True, confidence=0.85)
        all_ok &= check("CouncilResolution creation", res.consensus == True)
        all_ok &= check("CouncilResolution to_dict", isinstance(res.to_dict(), dict))

        # Default council factory
        council = create_default_council(kg=kg)
        all_ok &= check("create_default_council", len(council) == 5)

    except Exception as e:
        all_ok &= check(f"Council imports failed: {e}", False)
        import traceback

        traceback.print_exc()

    # L3: Council Orchestrator
    print("\n🎯 L3: Council Orchestrator")
    try:
        from iamsparta.council.orchestrator import CouncilOrchestrator

        orch = CouncilOrchestrator(kg=kg)
        all_ok &= check("Orchestrator creation", True)

        res = orch.analyze_tool("t1")
        all_ok &= check(
            "Orchestrator analyze_tool", res.confidence > 0 and len(res.opinions) >= 2
        )

        res = orch.compare_tools("t1", "t2")
        all_ok &= check("Orchestrator compare_tools", len(res.opinions) >= 3)

        res = orch.strategize("browser testing", domain="testing")
        all_ok &= check("Orchestrator strategize", len(res.opinions) >= 2)

        res = orch.full_audit()
        all_ok &= check("Orchestrator full_audit", len(res.opinions) > 0)

        res = orch.custom_run(["analyzer", "gap_finder"], {"tool_id": "t1"})
        all_ok &= check("Orchestrator custom_run", len(res.opinions) >= 2)

    except Exception as e:
        all_ok &= check(f"Orchestrator failed: {e}", False)
        import traceback

        traceback.print_exc()

    # Podsumowanie
    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 SPARTA: ALL CHECKS PASSED")
    else:
        print("⚠️  SPARTA: SOME CHECKS FAILED")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
