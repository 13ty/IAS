# Akceptacja Kryteriow — Heat Map

## Coverage

| Criterion                   | Threshold                         | Test                           |
| --------------------------- | --------------------------------- | ------------------------------ |
| **Domain analysis**         | 6 domains detected                | Verify all domains in registry |
| **Overlap detection**       | Detects visual overlap            | Verify 4 tools grouped         |
| **Port conflict detection** | Parses run_command correctly      | 10 test cases                  |
| **Strength/weakness**       | Identifies gaps (devops, ai)      | Verify 2 weaknesses            |
| **Bottleneck detection**    | Identifies critical single points | Verify 2 bottlenecks           |
| **Priority distribution**   | Counts hot/warm/cold correctly    | Verify 16 hot, 1 warm          |
| **Coverage score**          | 0.67 (4/6 domains)                | Verify calculation             |
| **Overlap score**           | 0.24 (4/17 tools)                 | Verify calculation             |

## Accuracy

| Criterion                 | Threshold                   | Test                      |
| ------------------------- | --------------------------- | ------------------------- |
| **Domain classification** | 100% correct                | Manual check on 16 tools  |
| **Port extraction**       | ≥ 90% accuracy              | 20 run_commands           |
| **Overlap precision**     | ≥ 80%                       | Manual check on 10 groups |
| **Strength/weakness**     | ≥ 85% agreement with expert | 10 domains                |

## Performance

| Criterion          | Threshold | Test      |
| ------------------ | --------- | --------- |
| **ASCII output**   | < 1s      | 16 tools  |
| **Mermaid output** | < 2s      | 16 tools  |
| **JSON output**    | < 1s      | 16 tools  |
| **Memory**         | < 50 MB   | 100 tools |

## Usability

| Criterion             | Threshold              | Test                |
| --------------------- | ---------------------- | ------------------- |
| **CLI exit codes**    | 0=ok, 1=error          | 3 test cases        |
| **ASCII readability** | Clear, formatted       | Visual inspection   |
| **Mermaid validity**  | Renders correctly      | Mermaid live editor |
| **JSON validity**     | Valid JSON             | `json.loads()`      |
| **File output**       | Creates file correctly | 3 test cases        |

## Security

| Criterion            | Threshold                  | Test               |
| -------------------- | -------------------------- | ------------------ |
| **Input validation** | No injection               | Malformed registry |
| **Path traversal**   | Rejected                   | `../../etc/passwd` |
| **Port validation**  | Only valid ports (1-65535) | Edge cases         |

## Dependencies

| Criterion              | Threshold           | Test                        |
| ---------------------- | ------------------- | --------------------------- |
| **tool_registry.json** | Must exist          | Verify file                 |
| **.envy**              | Optional (fallback) | Verify graceful degradation |
| **Python**             | 3.8+                | Version check               |

## Failure Recovery

| Scenario               | Behavior                             |
| ---------------------- | ------------------------------------ |
| **Missing registry**   | ❌ Fatal: "Brak rejestru narzędzi"   |
| **Missing .envy**      | ⚠️ Warning: "Pomijam analizę portów" |
| **Invalid JSON**       | ❌ Fatal: "Nieprawidłowy format"     |
| **Empty registry**     | ℹ️ "Brak narzędzi do analizy"        |
| **No ports**           | ℹ️ "Brak portów do analizy"          |
| **Keyboard interrupt** | Clean exit                           |

## Edge Cases

| Case                  | Expected Behavior                           |
| --------------------- | ------------------------------------------- |
| **Empty registry**    | All scores = 0, no strengths/weaknesses     |
| **Single tool**       | Works, identifies as bottleneck if critical |
| **All hot**           | No cold weaknesses                          |
| **All cold**          | All domains weak                            |
| **No alternatives**   | No overlaps detected                        |
| **Many alternatives** | Group correctly                             |
| **Port 0**            | Ignored (random port)                       |
| **Port 80/443**       | Ignored (default)                           |
| **Unicode in names**  | Handle correctly                            |
| **Windows paths**     | Normalize correctly                         |

## Performance Targets

| Scenario | Tools | Domains | Time   | Memory  |
| -------- | ----- | ------- | ------ | ------- |
| Empty    | 0     | 0       | < 0.1s | < 5 MB  |
| Small    | 5     | 3       | < 0.5s | < 10 MB |
| Standard | 16    | 6       | < 1s   | < 20 MB |
| Large    | 100   | 15      | < 3s   | < 50 MB |

## Changelog

| Version | Date       | Changes                     |
| ------- | ---------- | --------------------------- |
| 1.0     | 2024-06-08 | Initial acceptance criteria |
