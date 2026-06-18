# Akceptacja Kryteriow — Skaut

## Coverage

| Criterion                 | Threshold                               | Test                                 |
| ------------------------- | --------------------------------------- | ------------------------------------ |
| **Gap keyword mapping**   | All 10 categories covered               | Verify `GAP_KEYWORDS` keys           |
| **GitHub search**         | ≥ 80% success rate                      | 50 searches, check non-empty results |
| **Relevance scoring**     | 0-1 range, monotonic                    | 100 test repos                       |
| **Scorecard scoring**     | 0-1 range, monotonic                    | 100 test repos                       |
| **Final ranking**         | Top 10 sorted by score                  | Verify `results.sort()`              |
| **Gap coverage tracking** | Correct `gaps_covered` / `gaps_missing` | 20 test cases                        |
| **Language filtering**    | Respected when provided                 | 10 test cases                        |
| **Deduplication**         | No duplicate repos                      | Verify `all_repos` dict              |
| **JSON output**           | Valid JSON, all fields present          | Schema validation on 10 outputs      |
| **Text output**           | Human-readable format                   | Manual inspection                    |

## Accuracy

| Criterion                 | Threshold                          | Test                     |
| ------------------------- | ---------------------------------- | ------------------------ |
| **Relevance precision**   | ≥ 70%                              | Manual check on 50 repos |
| **Scorecard correlation** | r > 0.6 with manual quality rating | 30 repos                 |
| **Ranking quality**       | Top 3 repos relevant to gap        | 20 test cases            |
| **False positives**       | < 15%                              | 100 random repos         |
| **Coverage completeness** | ≥ 90% gaps covered                 | 20 test cases            |

## Performance

| Criterion               | Threshold               | Test                      |
| ----------------------- | ----------------------- | ------------------------- |
| **Search speed**        | < 5s per keyword        | 10 searches               |
| **Total execution**     | < 30s for 3 gaps        | 5 test cases              |
| **Memory usage**        | < 50 MB                 | 3 test cases              |
| **Rate limit handling** | Graceful when hit       | Test with 20+ searches    |
| **Timeout handling**    | Returns partial results | Test with slow connection |

## Usability

| Criterion              | Threshold               | Test              |
| ---------------------- | ----------------------- | ----------------- |
| **CLI exit codes**     | 0=ok, 1=error           | 3 test cases      |
| **Error messages**     | Clear, actionable       | 5 error scenarios |
| **Progress reporting** | Shows search keywords   | Visual inspection |
| **Output formats**     | JSON + text             | Verify both       |
| **File output**        | `--output` creates file | 3 test cases      |

## Security

| Criterion              | Threshold          | Test                    |
| ---------------------- | ------------------ | ----------------------- |
| **Input sanitization** | No shell injection | `"; rm -rf /"` test     |
| **Path traversal**     | Rejected           | `../../etc/passwd` test |
| **Rate limiting**      | Respected          | 20 rapid searches       |
| **Token handling**     | Never logged       | Verify logs             |

## Dependencies

| Criterion            | Threshold                | Test                   |
| -------------------- | ------------------------ | ---------------------- |
| **gh CLI installed** | Check on startup         | `check_gh_installed()` |
| **gh auth**          | Optional but recommended | Verify warning         |
| **Internet**         | Required                 | Clear error if offline |
| **Python**           | 3.8+                     | Version check          |

## Failure Recovery

| Scenario             | Behavior                                   |
| -------------------- | ------------------------------------------ |
| **gh not installed** | ❌ Clear error message, exit code 1        |
| **gh auth expired**  | ⚠️ Warning, continue with lower rate limit |
| **Rate limit hit**   | ⚠️ Warning, return partial results         |
| **Network timeout**  | ⚠️ Return partial results, log error       |
| **Invalid JSON**     | ⚠️ Skip repo, log error, continue          |
| **Empty results**    | ℹ️ "No results found" message              |
| **Unknown gap**      | ℹ️ Use gap name as keyword, fallback       |

## Edge Cases

| Case                       | Expected Behavior                       |
| -------------------------- | --------------------------------------- |
| **Empty gap list**         | ❌ Error: "--gaps required"             |
| **Single gap**             | Works normally                          |
| **10+ gaps**               | May hit rate limit, handle gracefully   |
| **Non-existent gap**       | Use gap name as keyword                 |
| **Language filter**        | Applied to all searches                 |
| **max-results=0**          | Return empty list                       |
| **max-results=100**        | Respect limit, may hit rate limit       |
| **No internet**            | ❌ Error: "gh search failed"            |
| **GitHub down**            | ❌ Error: timeout or connection refused |
| **Unicode in description** | Handle correctly                        |

## Performance Targets

| Scenario   | Gaps | Keywords | Time  | Memory  |
| ---------- | ---- | -------- | ----- | ------- |
| Single gap | 1    | 2        | < 5s  | < 10 MB |
| Standard   | 3    | 6        | < 15s | < 20 MB |
| Full scan  | 10   | 20       | < 60s | < 50 MB |

## Changelog

| Version | Date       | Changes                                    |
| ------- | ---------- | ------------------------------------------ |
| 1.0     | 2024-01-15 | Initial acceptance criteria                |
| 1.1     | 2024-02-01 | Added rate limit handling, timeout tests   |
| 1.2     | 2024-03-01 | Added accuracy metrics (precision, recall) |
| 1.3     | 2024-04-01 | Added edge cases for 10+ gaps              |
| 1.4     | 2024-05-01 | Added performance targets                  |
