---
title: "Akceptacja Kryteriow — Kwatermistrz (Root Skill)"
description: "Kryteria akceptacji dla głównego skill Kwatermistrza"
category: "acceptance-criteria"
skill: "kwatermistrz"
version: 1.0
---

# Akceptacja Kryteriow — Kwatermistrz (Root Skill)

## Coverage

| Criterion           | Threshold                                      | Test                            |
| ------------------- | ---------------------------------------------- | ------------------------------- |
| **Plugin manifest** | `plugin.json` valid, version ≥ 2.0.0           | JSON schema validation          |
| **Commands**        | 6 commands with frontmatter                    | Count + verify structure        |
| **Skills**          | 4 skills (inventory, scout, analyzer, auditor) | Count + verify SKILL.md         |
| **Scripts**         | 9 scripts, all executable                      | Count + verify shebang          |
| **Data**            | `tool_registry.json` + `proposals.csv`         | Verify structure                |
| **Agents**          | 1 orchestrator agent                           | Verify `agents/orchestrator.md` |
| **Hooks**           | 1 pre-commit hook                              | Verify `hooks/pre-commit.md`    |
| **References**      | 13 reference files                             | Count + verify content          |
| **Documentation**   | README.md + PLAN.md + VISION.md                | Verify completeness             |

## Accuracy

| Criterion            | Threshold                          | Test                      |
| -------------------- | ---------------------------------- | ------------------------- |
| **Self-audit**       | 0 issues, < 5 warnings             | Run `inventory_plugin.py` |
| **Security flags**   | All expected (subprocess, network) | Document each flag        |
| **Plugin inventory** | 100% files categorized             | Verify inventory output   |
| **File references**  | All paths resolve                  | Path validation           |

## Performance

| Criterion            | Threshold       | Test                       |
| -------------------- | --------------- | -------------------------- |
| **Plugin load**      | < 1s            | Time `plugin.json` parse   |
| **Script execution** | < 5s per script | 3 scripts                  |
| **Data loading**     | < 1s            | `tool_registry.json` parse |
| **Memory**           | < 100 MB        | 10 scripts running         |

## Usability

| Criterion                   | Threshold                     | Test                  |
| --------------------------- | ----------------------------- | --------------------- |
| **Command discoverability** | All commands in `plugin.json` | Verify manifest       |
| **Skill triggers**          | All trigger words work        | Test trigger matching |
| **Documentation**           | README explains all features  | Manual review         |
| **Error messages**          | Clear, actionable             | 5 error scenarios     |
| **Help text**               | All commands have --help      | Verify CLI parsers    |

## Security

| Criterion            | Threshold                 | Test                |
| -------------------- | ------------------------- | ------------------- |
| **Subprocess calls** | All documented, expected  | Security audit      |
| **Network calls**    | All documented, expected  | Security audit      |
| **File access**      | Within plugin directory   | Path traversal test |
| **Input validation** | All user inputs sanitized | Injection tests     |

## Integration

| Criterion      | Threshold                         | Test                  |
| -------------- | --------------------------------- | --------------------- |
| **3Pillars**   | Reads `.planCS` + `.envy`         | Verify integration    |
| **Vault**      | Writes to `Vaults/tool-registry/` | Verify output         |
| **LanceDB**    | Upserts to localhost:6542         | Verify connection     |
| **LMStudio**   | Embeddings via localhost:1234     | Verify API call       |
| **GitHub CLI** | `gh` commands work                | Verify `gh` installed |
| **Obsidian**   | Template v3 format                | Verify markdown       |

## Failure Recovery

| Scenario               | Behavior                            |
| ---------------------- | ----------------------------------- |
| **Missing config**     | Use defaults, log warning           |
| **LanceDB down**       | Fallback to JSON storage            |
| **LMStudio down**      | Skip embeddings, use keyword search |
| **GitHub CLI missing** | Clear error, install instructions   |
| **Vault missing**      | Fallback to `data/` directory       |
| **Permission denied**  | Clear error, suggest chmod          |
| **Corrupted data**     | Backup + reinitialize               |

## Edge Cases

| Case                      | Expected Behavior             |
| ------------------------- | ----------------------------- |
| **Empty plugin**          | Works with empty data         |
| **Single tool**           | Works with 1 tool in registry |
| **100 tools**             | Scales linearly               |
| **No proposals**          | ℹ️ "Brak propozycji"          |
| **All proposals audited** | ℹ️ "Wszystkie zaudytowane"    |
| **Unicode names**         | Handle correctly              |
| **Windows paths**         | Normalize to POSIX            |
| **Symlinks**              | Follow or skip (configurable) |
| **Nested directories**    | Recursive scan                |
| **Binary files**          | Skip silently                 |

## Performance Targets

| Scenario | Tools | Proposals | Time  | Memory   |
| -------- | ----- | --------- | ----- | -------- |
| Empty    | 0     | 0         | < 1s  | < 5 MB   |
| Small    | 5     | 5         | < 2s  | < 10 MB  |
| Standard | 16    | 10        | < 5s  | < 20 MB  |
| Large    | 100   | 50        | < 15s | < 50 MB  |
| Huge     | 500   | 200       | < 60s | < 100 MB |

## Changelog

| Version | Date       | Changes                                            |
| ------- | ---------- | -------------------------------------------------- |
| 1.0     | 2024-01-15 | Initial acceptance criteria                        |
| 1.1     | 2024-02-01 | Added integration tests (3Pillars, Vault, LanceDB) |
| 1.2     | 2024-03-01 | Added edge cases, performance targets              |
| 1.3     | 2024-04-01 | Added security criteria                            |
| 1.4     | 2024-05-01 | Added LMStudio integration                         |
| 2.0     | 2024-06-01 | Faza 2 complete, Kwatermistrz rebrand              |
