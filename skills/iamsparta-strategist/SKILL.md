# Skill: iamsparta-strategist

## Purpose

Agent Strateg IAmSparta — ocenia narzędzia i propozycje w kontekście strategicznym: jak pasują do ekosystemu, jaki mają potencjał i czy warto je adoptować. Wydaje rekomendacje TAKE / WAIT / BUILD / SKIP z uzasadnieniem.

## Trigger Phrases

- "jaka strategia dla \_"
- "czy warto użyć \_"
- "strategiczna ocena \_"
- "czy to pasuje do naszego stacka"
- "recommend strategy for \_"
- "assess \_ for our stack"
- "czy adoptować \_"

## Usage

```python
from iamsparta.council.agents import StrategistAgent
from iamsparta.kg.graph import KnowledgeGraph

kg = KnowledgeGraph()  # załadowany
strategist = StrategistAgent(kg=kg)

# Strategiczna ocena
result = strategist.strategize(
    goal="automated browser testing",
    domain="testing",
    context={"stack": ["python", "pytest"], "constraint": "must be open source"}
)

print(f"Rekomendacja: {result.recommendation}")
print(f"Confidence: {result.confidence}")
for action in result.proposed_actions:
    print(f"  ⚡ {action}")
```

## Decision Criteria

| Criterion             | Weight | Source                             |
| --------------------- | ------ | ---------------------------------- |
| Capability Fit        | 0.30   | KG + Semantic Search               |
| Quality & Maintenance | 0.20   | GitHub stars, last commit, license |
| Integration Cost      | 0.20   | .planCS, existing dependencies     |
| Community & Support   | 0.15   | Contributors, issues, docs         |
| Strategic Value       | 0.15   | Long-term alignment with stack     |

## Output

```json
{
  "goal": "automated browser testing",
  "recommendation": "TAKE",
  "confidence": 0.85,
  "rationale": "Playwright ma lepsze capability, pasuje do Python stacka...",
  "proposed_actions": [
    "Adopt playwright jako główne narzędzie do E2E",
    "Rozważ zastąpienie puppeteer"
  ],
  "alternatives_considered": ["selenium", "cypress", "puppeteer"]
}
```

## Dependencies

- `iamsparta` package
- Knowledge Graph z danymi o narzędziach
- (opcjonalnie) Semantic Search dla znajdowania podobnych narzędzi
