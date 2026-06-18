# Skill: iamsparta-feedback

## Purpose

Pętla feedbacku IAmSparta — uczenie się z decyzji i kalibracja confidence scoring. Zapisuje wyniki decyzji, porównuje z rzeczywistością i poprawia przyszłe rekomendacje.

## Trigger Phrases

- "feedback dla decyzji \_"
- "poprzednia decyzja o \_ była trafna"
- "zaktualizuj model o \_"
- "kalibracja confidence"
- "learn from decision \_"
- "feedback loop update"
- "co się sprawdziło z poprzednich rekomendacji"

## Usage

```python
from iamsparta.council.orchestrator import CouncilOrchestrator
from iamsparta.kg.graph import KnowledgeGraph

kg = KnowledgeGraph()
orch = CouncilOrchestrator(kg=kg)

# Feedback: decyzja była trafna
orch.record_feedback(
    decision_id="dec-20260601-001",
    outcome="success",  # success / failure / mixed
    notes="Playwright okazał się dobrym wyborem, spełnił oczekiwania"
)

# Feedback: decyzja nietrafna
orch.record_feedback(
    decision_id="dec-20260601-002",
    outcome="failure",
    notes="Narzędzie nie spełniło wymagań wydajnościowych"
)
```

## Feedback Schema

```json
{
  "decision_id": "dec-20260601-001",
  "tool": "playwright",
  "recommendation": "TAKE",
  "confidence_at_time": 0.85,
  "outcome": "success",
  "actual_value_delta": 0.0,
  "notes": "Spełnił oczekiwania",
  "recorded_at": "2026-06-15T10:00:00Z",
  "calibrated": false
}
```

## Calibration Process

1. Zbierz feedback dla N decyzji (min. 5 dla kalibracji)
2. Oblicz `accuracy = correct_predictions / total_decisions`
3. Jeśli accuracy < 0.7 → obniż confidence wszystkich agentów o 10%
4. Jeśli accuracy > 0.9 → podwyższ confidence o 5%
5. Zapisz zkalibrowane progi do `state/confidence_calibration.json`

## Dependencies

- `state/` katalog z historią decyzji
- CouncilOrchestrator z metodą record_feedback
