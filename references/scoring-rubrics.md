# Scoring Rubrics — IAS System

## 1. Technology Radar Classification

### Ring Criteria

| Ring | Criteria | Auto-classification Rule |
|------|----------|-------------------------|
| **Adopt** | Production-ready, recommended | Latest stable version, 0 CVEs, active maintenance |
| **Trial** | Worth exploring | ≤1 major version behind, minor CVEs only |
| **Assess** | Investigate for future | 1-2 major versions behind, some CVEs |
| **Hold** | Reconsider before use | EOL, critical CVEs, abandoned (>1 year no commits) |

### Version Freshness Scoring

```python
def version_freshness(current_version, latest_version):
    current = parse_semver(current_version)
    latest = parse_semver(latest_version)
    
    major_diff = latest.major - current.major
    minor_diff = latest.minor - current.minor
    
    if major_diff == 0 and minor_diff <= 1:
        return "adopt"
    elif major_diff == 0 or major_diff == 1:
        return "trial"
    elif major_diff == 2:
        return "assess"
    else:
        return "hold"
```

---

## 2. Clean Architecture Scoring

### Layer Detection (100 points total)

| Layer | Max Points | Detection Criteria |
|-------|------------|-------------------|
| **Entities** | 25 | Directory named `domain/`, `entities/`, `models/` exists |
| **Use Cases** | 25 | Directory named `usecases/`, `services/`, `interactors/` exists |
| **Adapters** | 25 | Directory named `adapters/`, `controllers/`, `gateways/` exists |
| **Drivers** | 25 | Directory named `infrastructure/`, `infra/`, `frameworks/` exists |

### Dependency Direction Violations

| Violation Type | Deduction |
|---------------|-----------|
| Inner layer imports outer layer | -15 per violation |
| Business logic in adapter layer | -10 per instance |
| Framework import in use case | -5 per import |
| Circular dependency | -20 per cycle |

### Final Score

```
CleanArchitectureScore = LayerScore - ViolationDeductions
Range: 0-100
```

---

## 3. Maintainability Index

### Formula (SEI Original)

```
MI = 171 - 5.2 × ln(HalsteadVolume) - 0.23 × CyclomaticComplexity - 16.2 × ln(LOC)
```

### Formula (Microsoft Normalized)

```
MI_normalized = MAX(0, (171 - 5.2 × ln(V) - 0.23 × G - 16.2 × ln(LOC)) × 100 / 171)
```

### Interpretation

| Score | Rating | Meaning |
|-------|--------|---------|
| 100-80 | 🟢 High | Easy to maintain, well-structured |
| 79-60 | 🟡 Moderate | Acceptable, some technical debt |
| 0-59 | 🔴 Low | High maintenance cost, needs refactoring |

### Component Weights

| Component | Impact | Formula Part |
|-----------|--------|--------------|
| Lines of Code | High (logarithmic) | -16.2 × ln(LOC) |
| Cyclomatic Complexity | Medium | -0.23 × G |
| Halstead Volume | Medium (logarithmic) | -5.2 × ln(V) |

---

## 4. Upgrade Value Calculation

### Weighted Components

| Component | Weight | Scoring Method |
|-----------|--------|----------------|
| **Feature Gap** | 30% | `features_target / features_current` |
| **Performance** | 25% | `benchmark_target / benchmark_current` |
| **Community** | 20% | `contributors_target / contributors_current` |
| **Learning Curve** | 15% | Inverse of documentation quality |
| **Migration Effort** | 10% | Estimated LOC changes / total LOC |

### Formula

```python
def upgrade_value(current, target):
    feature_gap = min(1.0, len(target.features) / max(1, len(current.features)))
    performance = min(1.0, target.benchmark / max(1, current.benchmark))
    community = min(1.0, target.contributors / max(1, current.contributors))
    learning = 1.0 - (target.docs_quality / 10.0)  # inverted
    migration = 1.0 - (target.effort / 10.0)  # inverted
    
    return (
        feature_gap * 0.30 +
        performance * 0.25 +
        community * 0.20 +
        learning * 0.15 +
        migration * 0.10
    )
```

### Interpretation

| Score | Recommendation |
|-------|----------------|
| 0.8-1.0 | Strong upgrade candidate |
| 0.6-0.8 | Consider for new projects |
| 0.4-0.6 | Evaluate carefully |
| 0.0-0.4 | Keep current stack |

---

## 5. OpenSSF Scorecard (Estimated)

### Scoring Criteria

| Check | Max Points | Detection Method |
|-------|------------|-----------------|
| Has SECURITY.md | 1 | File exists in repo root |
| Has LICENSE | 1 | License field in GitHub metadata |
| Active maintenance | 2 | Last commit <30 days ago |
| Has CI/CD | 2 | `.github/workflows/` exists |
| Has tests | 2 | `tests/` or `test/` directory exists |
| Good documentation | 2 | README.md >500 chars |

### Normalization

```
EstimatedScorecard = Sum(checks) / 10.0
Range: 0.0 - 1.0
```

---

## 6. Relevance Scoring

### Keyword Matching

```python
def relevance_score(repo_description, gap_keywords):
    repo_text = repo_description.lower()
    
    scores = []
    for keyword in gap_keywords:
        if keyword.lower() in repo_text:
            scores.append(1.0)
        else:
            # Fuzzy match
            scores.append(fuzzy_similarity(repo_text, keyword.lower()))
    
    return max(scores) if scores else 0.0
```

### Severity Weighting

| Severity | Weight |
|----------|--------|
| HIGH | 1.5 |
| MEDIUM | 1.0 |
| LOW | 0.5 |

---

## 7. Final Prioritization

### Composite Score

```python
final_score = (
    scorecard * 0.30 +
    criticality * 0.30 +
    relevance * 0.40
)
```

### Sorting

Results sorted descending by `final_score`.

### Diversity Requirement

Ensure at least 3 different gap categories are represented in top 10 results.
