# Akceptacja Kryteriow — Analizator

## Coverage

| Criterion                          | Threshold                           | Test                                           |
| ---------------------------------- | ----------------------------------- | ---------------------------------------------- |
| **Clean Architecture detection**   | ≥ 3 layers                          | `detect_layer()` on 4 sample paths             |
| **Dependency inversion detection** | 100% of violations                  | `check_violations()` on known-bad repo         |
| **Maintainability Index**          | MI ≥ 80 for "good" repos            | `calculate_maintainability()` on simple repo   |
| **LOC counting**                   | Exact (non-empty, non-comment)      | Manual count on 3 test files                   |
| **Complexity counting**            | ±1 from expected                    | Count if/elif/for/while/except on 5 files      |
| **Upgrade value**                  | Score 0-1, monotonic w.r.t. mi_diff | 5 test cases                                   |
| **Language support**               | Python, TS, JS, Go, Rust, C#        | `detect_layers()` on sample repos per language |

## Accuracy

| Criterion                 | Threshold                 | Test                                  |
| ------------------------- | ------------------------- | ------------------------------------- |
| **Layer false positives** | < 5%                      | 100 random paths, manual verification |
| **Layer false negatives** | < 10%                     | 50 known Clean Architecture paths     |
| **MI correlation**        | r > 0.7 with SonarQube MI | 10 repos, compare scores              |
| **Violation precision**   | ≥ 90%                     | 50 repos with known violations        |
| **Violation recall**      | ≥ 80%                     | 50 repos with known violations        |

## Performance

| Criterion          | Threshold              | Test                           |
| ------------------ | ---------------------- | ------------------------------ |
| **Analysis speed** | < 1s per 1000 LOC      | 5 repos of increasing size     |
| **Memory usage**   | < 50 MB per 1000 files | 3 repos                        |
| **Scalability**    | Linear in LOC          | O(n) verified on 100-10000 LOC |

## Usability

| Criterion              | Threshold                      | Test                            |
| ---------------------- | ------------------------------ | ------------------------------- |
| **CLI exit codes**     | 0=ok, 1=error, 2=violations    | 3 test cases                    |
| **JSON output**        | Valid JSON, all fields present | Schema validation on 10 outputs |
| **CSV output**         | Valid CSV, correct headers     | Manual inspection on 3 outputs  |
| **Error messages**     | Clear, actionable              | 5 error scenarios               |
| **Progress reporting** | > 90% accuracy                 | 10 repos, compare with expected |

## Security

| Criterion                    | Threshold          | Test                                       |
| ---------------------------- | ------------------ | ------------------------------------------ |
| **Path traversal**           | Rejected           | `../../etc/passwd` test                    |
| **Arbitrary code execution** | Rejected           | `__import__('os').system('rm -rf /')` test |
| **Resource exhaustion**      | Handled gracefully | 10 GB repo, OOM protection                 |

## Maintaining

| Criterion         | Threshold                       | Test               |
| ----------------- | ------------------------------- | ------------------ |
| **Test coverage** | ≥ 80%                           | `pytest --cov`     |
| **Documentation** | All public functions documented | `pydocstyle`       |
| **Type safety**   | All functions typed             | `mypy --strict`    |
| **Linting**       | Zero errors                     | `flake8` / `ruff`  |
| **Dependencies**  | Minimal, stable                 | `pip freeze` audit |

## Failure Recovery

| Scenario               | Behavior                                  |
| ---------------------- | ----------------------------------------- |
| **Non-existent repo**  | Exit code 1, clear error message          |
| **Unreadable file**    | Skip, log warning, continue               |
| **Parser error**       | Fallback to simple LOC count, log warning |
| **OOM**                | Graceful degradation, partial results     |
| **Keyboard interrupt** | Clean exit, partial results saved         |

## Edge Cases

| Case                        | Expected Behavior                       |
| --------------------------- | --------------------------------------- |
| **Empty repo**              | Score=0, all metrics=0, no crash        |
| **Single file**             | Accurate single-file metrics            |
| **No recognizable layers**  | Score=0, detected=0, no false positives |
| **All files in one layer**  | Score=25, no violations (same layer)    |
| **Symlinks**                | Follow or skip (configurable)           |
| **Binary files**            | Skip silently                           |
| **Very large files (>1MB)** | Skip with warning                       |
| **Unicode filenames**       | Handle correctly                        |
| **Windows paths**           | Normalize to POSIX                      |
| **Mixed languages**         | Analyze all supported, skip unsupported |

## Regression Tests

| Test                           | Frequency     | Description                                      |
| ------------------------------ | ------------- | ------------------------------------------------ |
| **Golden repos**               | Every release | 5 repos with known scores, compare with baseline |
| **Performance benchmark**      | Every release | 3 repos, time and memory                         |
| **CLI backward compatibility** | Every release | All old CLI flags still work                     |
| **JSON schema**                | Every change  | Validate against schema                          |

## Performance Targets

| Repo Size | LOC     | Files | Time   | Memory   |
| --------- | ------- | ----- | ------ | -------- |
| Tiny      | 100     | 5     | < 0.1s | < 5 MB   |
| Small     | 1000    | 20    | < 0.5s | < 10 MB  |
| Medium    | 10000   | 100   | < 2s   | < 25 MB  |
| Large     | 100000  | 500   | < 10s  | < 100 MB |
| Huge      | 1000000 | 2000  | < 60s  | < 500 MB |

## Changelog

| Version | Date       | Changes                                   |
| ------- | ---------- | ----------------------------------------- |
| 1.0     | 2024-01-15 | Initial acceptance criteria               |
| 1.1     | 2024-02-01 | Added performance targets, edge cases     |
| 1.2     | 2024-03-01 | Added regression tests, security criteria |
| 1.3     | 2024-04-01 | Added language support matrix             |
| 1.4     | 2024-05-01 | Added upgrade value criteria              |
| 1.5     | 2024-06-01 | Added OOM handling, resource exhaustion   |
