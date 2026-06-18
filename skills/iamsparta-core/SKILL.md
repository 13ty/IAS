# Skill: iamsparta-core

## Purpose

Główny orchestrator IAmSparta — routing między L1 (Knowledge Graph), L2 (Semantic Search) i L3 (Multi-Agent Council). Decyduje która warstwa odpowiada na pytanie, syntezuje odpowiedzi i zarządza confidence scoring.

## Trigger Phrases

- "uruchom IAmSparta"
- "co myślisz o \_"
- "jaka jest rekomendacja dla \_"
- "czy powinniśmy użyć \_"
- "zanalizuj ekosystem narzędzi"
- "IAmSparta full audit"
- "sparta analyze \_"
- "rada wojenna na temat \_"

## Usage

```python
from iamsparta.council.orchestrator import CouncilOrchestrator
from iamsparta.kg.graph import KnowledgeGraph
from iamsparta.kg.builder import build_graph

# Build graph
kg = build_graph()

# Create orchestrator
orch = CouncilOrchestrator(kg=kg)

# Analyze a tool
result = orch.analyze_tool("mcp-server-puppeteer")

# Compare two tools
result = orch.compare_tools("playwright", "puppeteer")

# Full ecosystem audit
result = orch.full_audit()

# Custom analysis run
result = orch.custom_run(
    agents=["analyzer", "strategist", "gapfinder"],
    tool_ids=["tool-a", "tool-b"]
)
```

## Layer Routing Logic

```
Pytanie użytkownika
  │
  ▼
L1 (KG) — szybka odpowiedź (< 1s)
  │
  ├── Confidence ≥ 0.8 → odpowiedź, koniec
  │
  ▼
L2 (Semantic Search) — rozszerzona (< 3s)
  │
  ├── Confidence ≥ 0.7 → odpowiedź, koniec
  │
  ▼
L3 (Multi-Agent Council) — pełna analiza (2-5 min)
  │
  ▼
  Synteza → TAKE / WAIT / BUILD / SKIP + confidence
```

## Council Agents

| Agent            | Role                            | When to activate     |
| ---------------- | ------------------------------- | -------------------- |
| AnalyzerAgent    | Analiza pojedynczego narzędzia  | Zawsze przy L3       |
| ComparatorAgent  | Porównanie dwóch narzędzi       | Gdy pytanie o wybór  |
| StrategistAgent  | Rekomendacja strategiczna       | Gdy potrzeba decyzji |
| GapFinderAgent   | Identyfikacja luk w ekosystemie | Przy audycie         |
| SynthesizerAgent | Synteza opinii w rezolucję      | Zawsze na końcu L3   |

## Decision Framework

| Decision  | When                             | Net Benefit  |
| --------- | -------------------------------- | ------------ |
| **TAKE**  | Zdecydowanie lepsze, niski koszt | > 5.0        |
| **WAIT**  | Warte uwagi, ale nie teraz       | > 0.0        |
| **BUILD** | Nikt nie robi tego dobrze        | Special case |
| **SKIP**  | Nie warto, mamy lub koszt > zysk | ≤ 0.0        |

## Dependencies

- Wszystkie warstwy iamsparta (graph, semantic, council agents)
- KnowledgeGraph z wczytanymi danymi
