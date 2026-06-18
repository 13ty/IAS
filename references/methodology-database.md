# Methodology Database — Smart Tech-Stack Oracle

## 1. Software Bill of Materials (SBOM)

### Standards
| Standard | Body | Focus |
|----------|------|-------|
| CycloneDX | OWASP | Security, DevSecOps |
| SPDX 3.0 | Linux Foundation | License compliance, multi-profile |
| SWID Tags | ISO/IEC 19770-2 | Enterprise asset management |

### Tools
| Tool | Formats | Strengths |
|------|---------|-----------|
| cdxgen | CycloneDX | Official OWASP, multi-language |
| syft | CycloneDX + SPDX | Fastest, container + FS |
| Microsoft SBOM Tool | SPDX | Enterprise scale |

---

## 2. Technology Radar

### Thoughtworks Model
**Quadrants**: Languages & Frameworks, Tools, Platforms, Techniques

**Rings**:
- **Adopt**: Production-ready, recommended
- **Trial**: Worth exploring
- **Assess**: Investigate for future
- **Hold**: Reconsider before use

### Extended Rings (Enterprise)
Some organizations add:
- **Consult**: Use with guidance
- **Experiment**: Early exploration
- **Retire**: Phase out

---

## 3. Clean Architecture (Robert C. Martin)

### Layers
1. **Entities**: Enterprise-wide business rules
2. **Use Cases**: Application-specific business rules
3. **Interface Adapters**: Data format converters
4. **Frameworks & Drivers**: External agencies (DB, Web, UI)

### Dependency Rule
Source code dependencies must point inward. Inner circles know nothing about outer circles.

### Evaluation Criteria
- Dependency direction enforcement
- Layer separation clarity
- Framework independence
- Testability without infrastructure

---

## 4. ATAM (Architecture Tradeoff Analysis Method)

### Developed by SEI/CMU
**Purpose**: Architecture evaluation through quality attribute scenarios

### Steps
1. Present ATAM
2. Present business drivers
3. Present architecture
4. Identify architecture approaches
5. Generate quality attribute utility tree
6. Analyze architecture approaches
7. Brainstorm and prioritize scenarios
8. Analyze architecture approaches (phase 2)
9. Present results

### Quality Attributes
- Performance
- Security
- Availability
- Modifiability
- Testability
- Usability

---

## 5. Maintainability Index (SEI)

### Formula
```
MI = 171 - 5.2 × ln(Halstead Volume) - 0.23 × (Cyclomatic Complexity) - 16.2 × ln(LOC)
```

### Microsoft Variant (normalized 0-100)
```
MI = MAX(0, (171 - 5.2 × ln(V) - 0.23 × G - 16.2 × ln(LOC)) × 100 / 171)
```

### Interpretation
- 100-80: High maintainability
- 79-60: Moderate
- 0-59: Low

---

## 6. OpenSSF Frameworks

### Scorecard
Automated security health (0-10 per check):
- Dangerous-Workflow
- Vulnerabilities
- Binary-Artifacts
- Token-Permissions
- Code-Review
- Maintained
- Branch-Protection
- Security-Policy

### Criticality Score
Project importance (0-1):
- Number of dependents
- Contributor count
- Release frequency
- GitHub signals

---

## 7. Architecture Decision Records (Martin Fowler)

### Format
```
# ADR-{number}: {Title}

## Status
{proposed | accepted | superseded}

## Context
{What is the issue that we're seeing that is motivating this decision?}

## Decision
{What is the change that we're proposing and/or doing?}

## Consequences
{What becomes easier or more difficult to do because of this change?}
```

### Rules
- One decision per record
- Never modify accepted ADRs — supersede them
- Monotonic numbering
- Inverted pyramid style (key info first)
