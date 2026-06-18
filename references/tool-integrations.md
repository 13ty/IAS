# Tool Integrations — IAS System

## External Tools

### 1. cdxgen (OWASP CycloneDX)

**Purpose**: Generate Software Bill of Materials (SBOM)

**Installation**:
```bash
npm install -g @cyclonedx/cdxgen
```

**Usage in IAS**:
```bash
cdxgen -t python -o sbom.json /path/to/project
```

**Output Format**: CycloneDX JSON

**Supported Ecosystems**:
- Node.js (package.json)
- Python (requirements.txt, pyproject.toml)
- Java (pom.xml, build.gradle)
- Go (go.mod)
- Rust (Cargo.toml)
- .NET (*.csproj)

**Fallback**: If not installed, parse manifest files directly.

---

### 2. grype (Anchore)

**Purpose**: Scan SBOM for known vulnerabilities

**Installation**:
```bash
# macOS
brew install grype

# Windows
winget install Anchore.grype

# Linux
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh
```

**Usage in IAS**:
```bash
grype sbom.json -o json > vulnerabilities.json
```

**Output Format**: JSON with CVE details

**Fallback**: If not installed, skip vulnerability scan.

---

### 3. gh CLI (GitHub)

**Purpose**: Search repositories, fetch metadata

**Installation**:
```bash
# macOS
brew install gh

# Windows
winget install GitHub.cli

# Linux
sudo apt install gh
```

**Authentication**:
```bash
gh auth login
```

**Usage in IAS**:
```bash
# Search repositories
gh search repos "pytest" --language python --stars ">100" --json name,url,stargazersCount

# Get repo metadata
gh api repos/pytest-dev/pytest --json stargazersCount,forkCount,updatedAt,license
```

**Rate Limits**:
- Unauthenticated: 10 requests/minute
- Authenticated: 30 requests/minute

---

### 4. OpenSSF Scorecard

**Purpose**: Security health assessment

**Installation**:
```bash
go install github.com/ossf/scorecard/v4@latest
```

**Usage in IAS**:
```bash
scorecard --repo=pytest-dev/pytest --format json
```

**Output Format**: JSON with check scores

**Alternative**: If not installed, use estimated scoring from GitHub metadata.

---

## Optional Tools

### syft (Anchore)

**Purpose**: Alternative SBOM generator (faster)

**Installation**:
```bash
brew install syft
# or
winget install Anchore.syft
```

**Usage**:
```bash
syft dir:/path/to/project -o cyclonedx-json > sbom.json
```

---

### trivy (Aqua Security)

**Purpose**: All-in-one security scanner

**Installation**:
```bash
brew install trivy
# or
winget install Aqua.Trivy
```

**Usage**:
```bash
trivy fs /path/to/project --format json > scan.json
```

---

## Python Libraries (for internal logic)

### AST Parsing

```python
import ast  # Built-in Python AST parser
```

### Text Similarity

```python
# Option 1: Built-in
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Option 2: External (optional)
# pip install python-Levenshtein
# from Levenshtein import ratio
```

### Semantic Version Parsing

```python
# pip install packaging
from packaging import version

v1 = version.parse("1.2.3")
v2 = version.parse("2.0.0")
if v2 > v1:
    print("Upgrade available")
```

---

## Error Handling Matrix

| Tool | Error | IAS Response |
|------|-------|--------------|
| cdxgen | Not installed | Fallback to manual parsing |
| cdxgen | Timeout | Retry once, then abort |
| grype | Not installed | Skip vulnerability scan |
| grype | CVE database outdated | Warn user, continue |
| gh | Rate limit | Exponential backoff |
| gh | Auth required | Prompt user to run `gh auth login` |
| scorecard | Not installed | Use estimated scoring |
| scorecard | Repo not accessible | Skip, note in report |
