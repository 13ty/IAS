# Acceptance Criteria: inventory skill

## Functional Requirements

| ID       | Requirement                                                                                               | Test                                                                |
| -------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **FR-1** | Detects ecosystems (Node, Python, .NET, Go, Rust, Java) via manifest files                                | `detect_ecosystems()` returns correct list for polyglot projects    |
| **FR-2** | Parses `package.json` (deps + devDeps) and `requirements.txt`/`pyproject.toml`                            | Components list includes name, version, type, ecosystem, radar_ring |
| **FR-3** | Classifies components on Technology Radar (adopt/trial/assess/hold) using known-good/known-outdated lists | `classify_radar()` produces 4 rings with correct assignments        |
| **FR-4** | Detects gaps: testing, docs, license, security, CI/CD, linting                                            | `detect_gaps()` returns Gap objects with category, severity, detail |
| **FR-5** | Calculates health score: coverage%, security risks, stale deps, gap count                                 | `calculate_health()` returns dict with coverage formula             |
| **FR-6** | Outputs JSON with `--json` and saves to file with `--output`                                              | CLI args `--json`, `--output` work correctly                        |

## Quality Gates

| ID       | Gate        | Criteria                                                    |
| -------- | ----------- | ----------------------------------------------------------- |
| **QG-1** | Performance | Runs in < 30s for typical project (≤500 deps)               |
| **QG-2** | Exit codes  | Exit 0 on success, non-zero on path not found / parse error |
| **QG-3** | Edge cases  | Empty directory → empty arrays, no crashes                  |
| **QG-4** | Determinism | Same input → identical JSON output                          |

## Integration Contract

| Interface      | Consumer                      | Format                                    |
| -------------- | ----------------------------- | ----------------------------------------- |
| **CLI**        | `/ias-inventory`, `/ias-scan` | stdin/stdout, JSON via `--json`           |
| **Python API** | `orchestrator.py`             | `scan_inventory(path) -> InventoryResult` |
| **Output**     | `orchestrator.py` Phase 1     | `result.gaps` → Scout keywords            |

## Data Structures

```python
@dataclass
class Component:
    name: str
    version: str
    type: str              # "library" | "devDependency"
    ecosystem: str         # "node" | "python" | ...
    radar_ring: str        # "adopt" | "trial" | "assess" | "hold"

@dataclass
class Gap:
    category: str          # "Testing" | "Documentation" | ...
    severity: str          # "high" | "medium" | "low"
    detail: str            # Human-readable description

@dataclass
class InventoryResult:
    path: str
    name: str
    timestamp: str         # ISO 8601
    ecosystems: List[str]
    components: List[Component]
    radar: Dict[str, List[str]]  # ring -> [names]
    gaps: List[Gap]
    health: Dict           # coverage, totalComponents, securityRisks, staleDependencies, gapCount
```

## References

| File                                 | Description                               |
| ------------------------------------ | ----------------------------------------- |
| `references/ecosystem-markers.md`    | Manifest files per ecosystem              |
| `references/radar-classification.md` | known_good / known_outdated per ecosystem |
| `references/gap-definitions.md`      | 6 gap categories + severity mapping       |
| `references/health-formula.md`       | Coverage formula + interpretation         |

## Test Cases (Manual)

```bash
# 1. Empty dir
python inventory_scan.py /tmp/empty --json
# → ecosystems: [], components: [], gaps: 6 (all categories), coverage: 0%

# 2. Node only (package.json with react, eslint)
python inventory_scan.py ./test-node --json
# → ecosystems: ["node"], radar: adopt=[react, eslint], gaps: 4 (no py/test)

# 3. Python only (requirements.txt with pytest, fastapi)
python inventory_scan.py ./test-python --json
# → ecosystems: ["python"], radar: adopt=[pytest, fastapi]

# 4. Polyglot (Node + Python)
python inventory_scan.py ./test-polyglot --json
# → ecosystems: ["node", "python"]

# 5. Perfect project (all gaps covered)
python inventory_scan.py ./test-perfect --json
# → gaps: [], coverage: 100%

# 6. Output to file
python inventory_scan.py ./project --json --output report.json
# → report.json created with valid JSON
```

## Non-Functional

- **Security**: No network calls, no subprocess (only stdlib `pathlib`, `json`)
- **Dependencies**: Zero external deps (stdlib only)
- **Portability**: Works on Windows (paths via `pathlib`), Linux, macOS
- **Encoding**: UTF-8 for all file reads

---

_Wersja: 1.0 | Skill: inventory | Ostatnia aktualizacja: 2026-06-08_
