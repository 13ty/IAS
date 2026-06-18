# Akceptacja Kryteriow — Auditor

## Coverage

| Criterion                   | Threshold                                   | Test                      |
| --------------------------- | ------------------------------------------- | ------------------------- |
| **Decision Matrix**         | 4 criteria × weights = 1.0                  | Verify weights sum to 1.0 |
| **Net Benefit calculation** | 0-10 range, monotonic                       | 20 test cases             |
| **Verdict thresholds**      | >7.0=adopt, >4.0=pilot, ≤4.0=lesson         | 20 test cases             |
| **Overlap detection**       | Detects existing tools by keyword           | 20 test cases             |
| **Gap analysis**            | Identifies feature/quality/integration gaps | 10 test cases             |
| **Report generation**       | Markdown with all sections                  | 5 test cases              |
| **CSV update**              | Status updated to "audited"                 | Verify `proposals.csv`    |
| **Vault integration**       | Writes to Obsidian vault                    | 3 test cases              |
| **Fallback to data/audits** | Works without vault                         | 3 test cases              |

## Accuracy

| Criterion                     | Threshold                  | Test                         |
| ----------------------------- | -------------------------- | ---------------------------- |
| **Overlap precision**         | ≥ 80%                      | Manual check on 20 repos     |
| **Overlap recall**            | ≥ 70%                      | 20 repos with known overlaps |
| **Gap fit correlation**       | r > 0.6 with expert rating | 20 repos                     |
| **Verdict agreement**         | ≥ 85% with expert panel    | 20 repos, 3 experts          |
| **False positives (overlap)** | < 15%                      | 50 random repos              |

## Performance

| Criterion            | Threshold              | Test         |
| -------------------- | ---------------------- | ------------ |
| **Audit speed**      | < 2s per proposal      | 20 proposals |
| **Batch audit**      | < 30s for 10 proposals | 3 test cases |
| **Memory usage**     | < 50 MB                | 10 proposals |
| **Registry loading** | < 1s                   | 3 test cases |

## Usability

| Criterion              | Threshold                  | Test              |
| ---------------------- | -------------------------- | ----------------- |
| **CLI exit codes**     | 0=ok, 1=error              | 3 test cases      |
| **Progress reporting** | Shows audit status         | Visual inspection |
| **Summary output**     | Verdict per proposal       | 5 test cases      |
| **Error messages**     | Clear, actionable          | 5 error scenarios |
| **Report readability** | Markdown renders correctly | 3 test cases      |

## Security

| Criterion              | Threshold            | Test                    |
| ---------------------- | -------------------- | ----------------------- | ------------------- |
| **Input sanitization** | No shell injection   | `"; rm -rf /"` test     |
| **Path traversal**     | Rejected             | `../../etc/passwd` test |
| **CSV injection**      | No formula injection | `=cmd                   | ' /C calc'!A0` test |

## Dependencies

| Criterion              | Threshold                          | Test               |
| ---------------------- | ---------------------------------- | ------------------ |
| **proposals.csv**      | Must exist                         | `load_proposals()` |
| **tool_registry.json** | Must exist                         | `load_registry()`  |
| **vault_writer**       | Optional (fallback to data/audits) | Verify fallback    |
| **Python**             | 3.8+                               | Version check      |

## Failure Recovery

| Scenario               | Behavior                                    |
| ---------------------- | ------------------------------------------- |
| **No proposals.csv**   | ❌ Error: "Brak proposals.csv"              |
| **Empty proposals**    | ℹ️ "Brak propozycji"                        |
| **Invalid URL**        | ⚠️ Warning, skip, continue                  |
| **Registry not found** | ⚠️ Use empty registry, no overlap detection |
| **Vault writer error** | ⚠️ Fallback to `data/audits/`               |
| **Permission denied**  | ❌ Error, clear message                     |
| **Keyboard interrupt** | Clean exit, partial results saved           |

## Edge Cases

| Case                      | Expected Behavior                           |
| ------------------------- | ------------------------------------------- |
| **Single proposal**       | Works normally                              |
| **100 proposals**         | Batch process, progress reporting           |
| **No overlap**            | Gap Fit = default (7)                       |
| **Multiple overlaps**     | Gap Fit = max(1, 7 - 3) = 4                 |
| **All proposals audited** | ℹ️ "Wszystkie zaudytowane"                  |
| **Mixed statuses**        | `--all` processes all, default only pending |
| **Invalid --id**          | ❌ Error: index out of range                |
| **Unicode in notes**      | Handle correctly                            |
| **Very long notes**       | Truncate in output, preserve in CSV         |
| **Missing type**          | Default to "repo"                           |

## Performance Targets

| Scenario    | Proposals | Time  | Memory  |
| ----------- | --------- | ----- | ------- |
| Single      | 1         | < 2s  | < 10 MB |
| Standard    | 10        | < 15s | < 20 MB |
| Large batch | 100       | < 60s | < 50 MB |

## Changelog

| Version | Date       | Changes                                 |
| ------- | ---------- | --------------------------------------- |
| 1.0     | 2024-01-15 | Initial acceptance criteria             |
| 1.1     | 2024-02-01 | Added vault integration, fallback tests |
| 1.2     | 2024-03-01 | Added edge cases for 100+ proposals     |
| 1.3     | 2024-04-01 | Added security criteria (CSV injection) |
| 1.4     | 2024-05-01 | Added performance targets               |
