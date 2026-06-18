# Skill: iamsparta-comparison

## Purpose

Silnik porównawczy IAmSparta — analizuje dwa lub więcej narzędzi pod kątem różnic funkcjonalnych, capability gap, kosztów integracji i redundancji. Używany przez L3 Council gdy potrzeba decyzji "które narzędzie wybrać".

## Trigger Phrases

- "porównaj _ i _"
- "które lepsze do \_"
- "różnica między _ a _"
- "compare _ and _"
- "which tool for \_"
- "feature comparison _ vs _"
- "co wybrać do \_"

## Usage

```python
from iamsparta.council.orchestrator import CouncilOrchestrator
from iamsparta.kg.graph import KnowledgeGraph

kg = KnowledgeGraph()  # załadowany
orch = CouncilOrchestrator(kg=kg)

# Porównanie dwóch narzędzi
result = orch.compare_tools("mcp-server-puppeteer", "playwright")

# Wynik
print(f"Konsensus: {result.consensus}")
print(f"Pewność: {result.confidence}")

# Opinie agentów
for opinion in result.opinions:
    print(f"[{opinion.role.value}] {opinion.agent_id}")
    for rec in opinion.recommendations:
        print(f"  ⚡ {rec}")
```

## Comparison Dimensions

| Dimension        | Source           | Description                          |
| ---------------- | ---------------- | ------------------------------------ |
| Capability Gap   | KG + Semantic    | Czego brakuje jednemu a ma drugie    |
| Quality Delta    | metadata         | Różnica w quality_score, maintenance |
| Integration Cost | .planCS + .envy  | Koszt wdrożenia w środowisku         |
| Redundancy       | KG overlaps_with | Czy narzędzia się dublują            |

## Output

```json
{
  "tool_a": "mcp-server-puppeteer",
  "tool_b": "playwright",
  "capability_gap": { "a_missing": ["video"], "b_missing": ["pdf"] },
  "quality_delta": 0.15,
  "integration_cost": "medium",
  "redundancy": 0.7,
  "recommendation": "playwright — szersze capability, lepsza jakość",
  "confidence": 0.82
}
```

## Dependencies

- `iamsparta` package
- Knowledge Graph z narzędziami i relacjami
