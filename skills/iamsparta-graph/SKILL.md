# Skill: iamsparta-graph

## Purpose

Knowledge Graph IAmSparta — relacje między narzędziami, capability map, analiza nakładania i luk w ekosystemie. Odpowiada na pytania o zależności, alternatywy i zastąpienia.

## Trigger Phrases

- "pokaż relacje dla \_"
- "co jest alternatywą dla \_"
- "jakie narzędzia w domenie \_"
- "znajdź nakładające się narzędzia"
- "pokaż luki w ekosystemie"
- "find tool \_"
- "show alternatives for \_"
- "graph overview"

## Usage

```python
from iamsparta.kg.graph import KnowledgeGraph
from iamsparta.kg.builder import KnowledgeGraphBuilder
from iamsparta.kg.query import KnowledgeGraphQuery

# Build KG from tool registry
builder = KnowledgeGraphBuilder()
kg = builder.build_from_registry("data/tool_registry.json")
query = KnowledgeGraphQuery(kg)

# Find tool
tool = query.find_tool("mcp-server-puppeteer")

# Get alternatives
alts = query.get_alternatives(tool.id)

# Full report
report = query.full_report()
```

## Data Sources

| Source         | Location                                                      | Description                            |
| -------------- | ------------------------------------------------------------- | -------------------------------------- |
| Tool Registry  | `data/tool_registry.json`                                     | Główny rejestr narzędzi IAS (16 tools) |
| Tool Inventory | `~/.config/opencode/Vaults/tool-registry/tool_inventory.json` | Pełny inwentarz z archiwum             |
| .planCS        | `backend/.planCS`                                             | Mapa rusztowania katalogów             |
| .envy          | `backend/.envy`                                               | Porty i zależności zewnętrzne          |

## Relationship Types

| Type            | Meaning                       | Auto-inferred                      |
| --------------- | ----------------------------- | ---------------------------------- |
| `DEPENDS_ON`    | A wymaga B                    | Nie                                |
| `REPLACES`      | A zastępuje B                 | Tak (z alternatyw deprecated)      |
| `REPLACED_BY`   | A jest zastąpione przez B     | Tak (z alternatyw deprecated)      |
| `ALTERNATIVE`   | A może być zamiennikiem B     | Tak (z alternatyw w tool_data)     |
| `OVERLAPS_WITH` | A i B mają wspólne capability | Tak (ta sama domena)               |
| `COMPLEMENTARY` | A i B uzupełniają się         | Tak (ta sama domena, słabsza waga) |

## Output Format

```json
{
  "tools": {"count": 16, "by_domain": {"visual": 4, "testing": 3, ...}},
  "domains": [{"id": "visual", "tools": ["remotion", "plantuml", ...]}],
  "gaps": [{"domain": "devops", "severity": "high", "suggestion": "..."]],
  "relationships": [{"source_id": "...", "rel_type": "overlaps_with", "weight": 0.7}]
}
```

## Dependencies

- `iamsparta` package installed (editable: `scripts/iamsparta/`)
- `data/tool_registry.json` — musi istnieć
