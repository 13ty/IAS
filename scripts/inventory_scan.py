#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import re
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
import xml.etree.ElementTree as ET
import configparser

try:
    import tomllib
except ImportError:
    tomllib = None


IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    ".DS_Store",
    ".ruff_cache",
    "__pypackages__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "eggs",
    "wheelhouse",
    ".gitlab",
    ".terraform",
    ".serverless",
    "coverage",
    ".nyc_output",
    "bower_components",
    ".svelte-kit",
    ".cache",
    ".npm",
}

ECOSYSTEM_MARKERS = {
    "node": [("package.json", "file")],
    "python": [
        ("requirements.txt", "file"),
        ("pyproject.toml", "file"),
        ("setup.py", "file"),
        ("setup.cfg", "file"),
        ("Pipfile", "file"),
    ],
    "rust": [("Cargo.toml", "file")],
    "go": [("go.mod", "file")],
    "java": [("pom.xml", "file"), ("build.gradle", "file")],
    "dotnet": [("*.csproj", "glob"), ("*.sln", "glob")],
    "ruby": [("Gemfile", "file")],
    "php": [("composer.json", "file")],
}

EXTENSION_LANG = {
    ".py": "python",
    ".pyi": "python",
    ".pyx": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".jsp": "java",
    ".cs": "csharp",
    ".cshtml": "csharp",
    ".rb": "ruby",
    ".erb": "ruby",
    ".php": "php",
    ".phtml": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".vue": "vue",
    ".svelte": "svelte",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".html": "html",
    ".htm": "html",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".mdx": "markdown",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".psd1": "powershell",
    ".tf": "terraform",
    ".tfvars": "terraform",
    ".hcl": "hcl",
    ".dockerfile": "dockerfile",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".xml": "xml",
    ".xsl": "xml",
    ".cmake": "cmake",
    ".lua": "lua",
    ".r": "r",
    ".rmd": "r",
    ".dart": "dart",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hrl": "erlang",
    ".hs": "haskell",
    ".lhs": "haskell",
    ".clj": "clojure",
    ".cljs": "clojure",
    ".cljc": "clojure",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".dockerignore": "docker",
    ".editorconfig": "editorconfig",
    ".gitignore": "git",
}

FRAMEWORK_PATTERNS = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
    "aiohttp": "aiohttp",
    "tornado": "Tornado",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "alembic": "Alembic",
    "celery": "Celery",
    "redis": "Redis",
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "vue": "Vue.js",
    "nuxt": "Nuxt.js",
    "pinia": "Pinia",
    "angular": "Angular",
    "@angular/core": "Angular",
    "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit",
    "express": "Express",
    "fastify": "Fastify",
    "socket.io": "Socket.IO",
    "prisma": "Prisma",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "tailwindcss": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "vitest": "Vitest",
    "jest": "Jest",
    "mocha": "Mocha",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "spring-boot": "Spring Boot",
    "spring-boot-starter": "Spring Boot",
    "hibernate": "Hibernate",
    "junit": "JUnit",
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "pandas": "pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "actix-web": "Actix Web",
    "rocket": "Rocket",
    "tokio": "Tokio",
    "serde": "Serde",
    "gin": "Gin",
    "echo": "Echo",
    "fiber": "Fiber",
    "gorm": "GORM",
    "cobra": "Cobra",
    "rails": "Ruby on Rails",
    "rack": "Rack",
    "laravel": "Laravel",
    "symfony": "Symfony",
    "aspnet": "ASP.NET Core",
    "microsoft.aspnetcore": "ASP.NET Core",
    "entity-framework": "Entity Framework Core",
    "transformers": "HuggingFace Transformers",
    "datasets": "HuggingFace Datasets",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "httpx": "HTTPX",
    "requests": "Requests",
    "click": "Click",
    "typer": "Typer",
    "rich": "Rich",
    "polars": "Polars",
    "duckdb": "DuckDB",
    "apache-beam": "Apache Beam",
    "pyspark": "Apache Spark",
    "dagger": "Dagger",
    "gradle": "Gradle",
    "discord.py": "Discord.py",
    "flask-sqlalchemy": "Flask-SQLAlchemy",
    "marshmallow": "Marshmallow",
    "attrs": "attrs",
    "cattrs": "cattrs",
    "orjson": "orjson",
}

FRAMEWORK_CONTAINS = {
    "@angular/": "Angular",
    "@nestjs/": "NestJS",
    "@aws-sdk": "AWS SDK",
    "@azure/": "Azure SDK",
    "@mui/": "Material UI",
    "@radix-ui": "Radix UI",
    "@headlessui": "Headless UI",
    "@shadcn/ui": "shadcn/ui",
    "@tanstack": "TanStack Query",
    "eslint-": "ESLint",
    "babel-": "Babel",
    "webpack": "Webpack",
    "vite": "Vite",
    "rollup": "Rollup",
    "parcel": "Parcel",
    "turbo": "Turborepo",
}

GAP_DEFINITIONS = {
    "testing": {
        "severity": "high",
        "detail": "No test files or test framework detected",
        "recommendation": "Add test framework (pytest for Python, vitest/jest for JS/TS) and write unit tests",
    },
    "ci_cd": {
        "severity": "medium",
        "detail": "No CI/CD configuration detected",
        "recommendation": "Set up GitHub Actions, GitLab CI, or similar CI/CD pipeline",
    },
    "docker": {
        "severity": "medium",
        "detail": "No Dockerfile detected",
        "recommendation": "Add Dockerfile for containerized deployment and docker-compose.yml for multi-service setup",
    },
    "readme": {
        "severity": "medium",
        "detail": "No README.md found",
        "recommendation": "Create README.md with project description, setup instructions, architecture overview, and usage guide",
    },
    "license": {
        "severity": "medium",
        "detail": "No LICENSE file found",
        "recommendation": "Add an open-source license (MIT, Apache 2.0, or GPL-3.0)",
    },
    "linting": {
        "severity": "low",
        "detail": "No linter or formatter configuration detected",
        "recommendation": "Configure linter (ruff for Python, ESLint for JS/TS) and formatter (Black/prettier)",
    },
    "security": {
        "severity": "low",
        "detail": "No security policy or vulnerability scanning detected",
        "recommendation": "Add SECURITY.md and enable Dependabot or similar dependency vulnerability scanning",
    },
    "changelog": {
        "severity": "low",
        "detail": "No CHANGELOG.md found",
        "recommendation": "Maintain a changelog following keepachangelog.com format",
    },
    "contributing": {
        "severity": "low",
        "detail": "No CONTRIBUTING.md found",
        "recommendation": "Add CONTRIBUTING.md with development setup and contribution guidelines",
    },
    "codeowners": {
        "severity": "low",
        "detail": "No CODEOWNERS file found",
        "recommendation": "Add .github/CODEOWNERS for PR review assignments",
    },
    "docker_compose": {
        "severity": "low",
        "detail": "No docker-compose.yml found",
        "recommendation": "Add docker-compose.yml for local development environment",
    },
    "env_example": {
        "severity": "low",
        "detail": "No .env.example or .env.template found",
        "recommendation": "Add .env.example with required environment variables documented",
    },
    "makefile": {
        "severity": "low",
        "detail": "No Makefile found",
        "recommendation": "Add Makefile with common commands (install, test, lint, build)",
    },
}


def clean_version(ver: str) -> str:
    return re.sub(r"^[\^~>=<!]+\s*", "", ver).strip()


def is_ignored(parts) -> bool:
    return any(p in IGNORE_DIRS for p in parts)


def detect_ecosystems(root: Path) -> List[str]:
    ecosystems = []
    for eco, markers in ECOSYSTEM_MARKERS.items():
        for marker, method in markers:
            if method == "file":
                if (root / marker).exists():
                    ecosystems.append(eco)
                    break
            elif method == "glob":
                if list(root.glob(marker)):
                    ecosystems.append(eco)
                    break
    return ecosystems


def parse_package_json(pkg_file: Path) -> List[Dict]:
    components = []
    try:
        with open(pkg_file, encoding="utf-8") as f:
            pkg = json.load(f)
        for name, ver in pkg.get("dependencies", {}).items():
            components.append(
                {
                    "name": name,
                    "version": clean_version(ver),
                    "ecosystem": "npm",
                    "type": "direct",
                }
            )
        for name, ver in pkg.get("devDependencies", {}).items():
            components.append(
                {
                    "name": name,
                    "version": clean_version(ver),
                    "ecosystem": "npm",
                    "type": "dev",
                }
            )
    except Exception:
        pass
    return components


def parse_requirements_txt(req_file: Path) -> List[Dict]:
    components = []
    try:
        with open(req_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(("#", "-", "//", "--")):
                    continue
                m = re.match(r"^([a-zA-Z0-9_.-]+)\s*([><=!~]+\s*[\w.*]+)?", line)
                if m:
                    name = m.group(1).strip()
                    ver = "latest"
                    if m.group(2):
                        ver = re.sub(r"^[><=!~]+\s*", "", m.group(2).strip())
                    components.append(
                        {
                            "name": name,
                            "version": ver,
                            "ecosystem": "pip",
                            "type": "direct",
                        }
                    )
    except Exception:
        pass
    return components


def parse_pyproject_toml(toml_file: Path) -> List[Dict]:
    components = []
    if tomllib is None:
        return components
    try:
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return components

    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        m = re.match(r"^([a-zA-Z0-9_.-]+)\s*(.*)", dep)
        if m:
            name = m.group(1)
            ver = "latest"
            vm = re.search(r"[><=!~]+\s*[\w.*]+", m.group(2))
            if vm:
                ver = re.sub(r"^[><=!~]+\s*", "", vm.group(0))
            components.append(
                {"name": name, "version": ver, "ecosystem": "pip", "type": "direct"}
            )

    for group_deps in project.get("optional-dependencies", {}).values():
        for dep in group_deps:
            m = re.match(r"^([a-zA-Z0-9_.-]+)\s*(.*)", dep)
            if m:
                name = m.group(1)
                ver = "latest"
                vm = re.search(r"[><=!~]+\s*[\w.*]+", m.group(2))
                if vm:
                    ver = re.sub(r"^[><=!~]+\s*", "", vm.group(0))
                components.append(
                    {"name": name, "version": ver, "ecosystem": "pip", "type": "dev"}
                )

    build_system = data.get("build-system", {})
    if build_system.get("requires"):
        for dep in build_system["requires"]:
            m = re.match(r"^([a-zA-Z0-9_.-]+)\s*(.*)", dep)
            if m:
                name = m.group(1)
                ver = "latest"
                vm = re.search(r"[><=!~]+\s*[\w.*]+", m.group(2))
                if vm:
                    ver = re.sub(r"^[><=!~]+\s*", "", vm.group(0))
                components.append(
                    {"name": name, "version": ver, "ecosystem": "pip", "type": "dev"}
                )

    tool_poetry = data.get("tool", {}).get("poetry", {})
    for name, ver in tool_poetry.get("dependencies", {}).items():
        if name.lower() == "python":
            continue
        if isinstance(ver, dict):
            ver = ver.get("version", "latest")
        components.append(
            {
                "name": name,
                "version": clean_version(str(ver)),
                "ecosystem": "pip",
                "type": "direct",
            }
        )
    for name, ver in tool_poetry.get("dev-dependencies", {}).items():
        if isinstance(ver, dict):
            ver = ver.get("version", "latest")
        components.append(
            {
                "name": name,
                "version": clean_version(str(ver)),
                "ecosystem": "pip",
                "type": "dev",
            }
        )

    return components


def parse_cargo_toml(cargo_file: Path) -> List[Dict]:
    components = []
    try:
        if tomllib is not None:
            with open(cargo_file, "rb") as f:
                data = tomllib.load(f)
        else:
            parser = configparser.ConfigParser()
            with open(cargo_file, encoding="utf-8") as f:
                parser.read_string("[root]\n" + f.read())
            data = (
                {"dependencies": dict(parser.items("dependencies"))}
                if parser.has_section("dependencies")
                else {}
            )
            if parser.has_section("dev-dependencies"):
                data["dev-dependencies"] = dict(parser.items("dev-dependencies"))
    except Exception:
        try:
            data = {}
            current_section = "root"
            with open(cargo_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line[1:-1].strip()
                        data[current_section] = {}
                    elif "=" in line and current_section in (
                        "dependencies",
                        "dev-dependencies",
                    ):
                        k, _, v = line.partition("=")
                        data[current_section][k.strip()] = v.strip().strip('"')
        except Exception:
            return components

    for name, ver in data.get("dependencies", {}).items():
        if isinstance(ver, dict):
            ver = ver.get("version", "latest")
        components.append(
            {
                "name": name,
                "version": clean_version(str(ver)),
                "ecosystem": "cargo",
                "type": "direct",
            }
        )
    for name, ver in data.get("dev-dependencies", {}).items():
        if isinstance(ver, dict):
            ver = ver.get("version", "latest")
        components.append(
            {
                "name": name,
                "version": clean_version(str(ver)),
                "ecosystem": "cargo",
                "type": "dev",
            }
        )
    for name, ver in data.get("build-dependencies", {}).items():
        if isinstance(ver, dict):
            ver = ver.get("version", "latest")
        components.append(
            {
                "name": name,
                "version": clean_version(str(ver)),
                "ecosystem": "cargo",
                "type": "dev",
            }
        )
    return components


def parse_go_mod(mod_file: Path) -> List[Dict]:
    components = []
    try:
        with open(mod_file, encoding="utf-8") as f:
            in_require = False
            for line in f:
                stripped = line.strip()
                if stripped.startswith("require ("):
                    in_require = True
                elif stripped == ")":
                    in_require = False
                elif in_require and stripped:
                    parts = stripped.split()
                    if len(parts) >= 2:
                        components.append(
                            {
                                "name": parts[0],
                                "version": parts[1],
                                "ecosystem": "go",
                                "type": "direct",
                            }
                        )
                elif stripped.startswith("require ") and not stripped.endswith("("):
                    m = re.match(r"require\s+(\S+)\s+(\S+)", stripped)
                    if m:
                        components.append(
                            {
                                "name": m.group(1),
                                "version": m.group(2),
                                "ecosystem": "go",
                                "type": "direct",
                            }
                        )
    except Exception:
        pass
    return components


def parse_pom_xml(pom_file: Path) -> List[Dict]:
    components = []
    try:
        tree = ET.parse(pom_file)
        root = tree.getroot()
        ns = re.match(r"\{.*\}", root.tag)
        ns = ns.group(0) if ns else ""

        props = {}
        for prop in root.findall(f".//{ns}properties/*"):
            props[prop.tag.replace(ns, "")] = prop.text or ""

        def resolve(v):
            m = re.match(r"\$\{(.+)\}", v)
            return props.get(m.group(1), v) if m else v

        parent = root.find(f"{ns}parent")
        if parent is not None:
            g = parent.find(f"{ns}groupId")
            a = parent.find(f"{ns}artifactId")
            v = parent.find(f"{ns}version")
            if g is not None and a is not None and v is not None:
                components.append(
                    {
                        "name": f"{g.text}:{a.text}",
                        "version": resolve(v.text or ""),
                        "ecosystem": "maven",
                        "type": "direct",
                    }
                )

        for dep in root.findall(f".//{ns}dependencies/{ns}dependency"):
            g = dep.find(f"{ns}groupId")
            a = dep.find(f"{ns}artifactId")
            v = dep.find(f"{ns}version")
            scope_el = dep.find(f"{ns}scope")
            if g is not None and a is not None:
                name = f"{g.text}:{a.text}"
                version = resolve(v.text) if v is not None and v.text else "latest"
                dep_type = (
                    "dev"
                    if scope_el is not None and scope_el.text == "test"
                    else "direct"
                )
                components.append(
                    {
                        "name": name,
                        "version": version,
                        "ecosystem": "maven",
                        "type": dep_type,
                    }
                )
    except Exception:
        pass
    return components


def parse_gemfile(gem_file: Path) -> List[Dict]:
    components = []
    try:
        with open(gem_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                m = re.match(r"^\s*gem\s+['\"](.+?)['\"]", line)
                if m:
                    name = m.group(1)
                    ver = "latest"
                    vm = re.search(r"['\"]([><=~!]+\s*[\w.]+)['\"]", line)
                    if vm:
                        ver = re.sub(r"^[><=~!]+\s*", "", vm.group(1))
                    dep_type = (
                        "dev"
                        if "group :development" in line or "group :test" in line
                        else "direct"
                    )
                    components.append(
                        {
                            "name": name,
                            "version": ver,
                            "ecosystem": "gem",
                            "type": dep_type,
                        }
                    )
    except Exception:
        pass
    return components


def parse_composer_json(composer_file: Path) -> List[Dict]:
    components = []
    try:
        with open(composer_file, encoding="utf-8") as f:
            data = json.load(f)
        for name, ver in data.get("require", {}).items():
            components.append(
                {
                    "name": name,
                    "version": clean_version(ver),
                    "ecosystem": "packagist",
                    "type": "direct",
                }
            )
        for name, ver in data.get("require-dev", {}).items():
            components.append(
                {
                    "name": name,
                    "version": clean_version(ver),
                    "ecosystem": "packagist",
                    "type": "dev",
                }
            )
    except Exception:
        pass
    return components


def parse_setup_cfg(cfg_file: Path) -> List[Dict]:
    components = []
    try:
        parser = configparser.ConfigParser()
        parser.read(cfg_file)
        if parser.has_section("options"):
            deps = parser.get("options", "install_requires", fallback="")
            for dep in re.split(r"[\n,]", deps):
                dep = dep.strip()
                if dep:
                    m = re.match(r"^([a-zA-Z0-9_.-]+)\s*(.*)", dep)
                    if m:
                        name = m.group(1)
                        ver = "latest"
                        vm = re.search(r"[><=!~]+\s*[\w.*]+", m.group(2))
                        if vm:
                            ver = re.sub(r"^[><=!~]+\s*", "", vm.group(0))
                        components.append(
                            {
                                "name": name,
                                "version": ver,
                                "ecosystem": "pip",
                                "type": "direct",
                            }
                        )
    except Exception:
        pass
    return components


def _probe_tool(name: str, timeout: int = 5) -> bool:
    try:
        subprocess.run([name, "--version"], capture_output=True, timeout=timeout)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError, OSError):
        return False


def try_cdxgen(root: Path) -> Optional[Dict]:
    if not _probe_tool("cdxgen", 5):
        return None
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        result = subprocess.run(
            ["cdxgen", "-o", tmp_path, "-r", str(root)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return None
        with open(tmp_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def try_grype(root: Path) -> Optional[Dict]:
    if not _probe_tool("grype", 5):
        return None
    try:
        result = subprocess.run(
            ["grype", "dir:" + str(root), "-o", "json"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def try_cloc(root: Path) -> Optional[Dict]:
    if not _probe_tool("cloc", 5):
        return None
    try:
        result = subprocess.run(
            ["cloc", str(root), "--json", "--quiet"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def analyze_files(root: Path) -> Dict[str, Dict[str, int]]:
    languages = defaultdict(lambda: {"files": 0, "loc": 0})
    try:
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if is_ignored(f.parts):
                continue
            ext = f.suffix.lower()
            lang = EXTENSION_LANG.get(ext)
            if not lang:
                name = f.name.lower()
                if name == "dockerfile":
                    lang = "dockerfile"
                elif name in (".gitignore",):
                    lang = "git"
                elif name in (".editorconfig",):
                    lang = "editorconfig"
                else:
                    continue
            languages[lang]["files"] += 1
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    languages[lang]["loc"] += sum(1 for _ in fh)
            except Exception:
                pass
    except Exception:
        pass
    return dict(languages)


def detect_frameworks(components: List[Dict]) -> List[str]:
    frameworks = set()
    for c in components:
        name = c["name"].lower()
        if name in FRAMEWORK_PATTERNS:
            frameworks.add(FRAMEWORK_PATTERNS[name])
            continue
        for prefix, fw in FRAMEWORK_CONTAINS.items():
            if name.startswith(prefix.lower()):
                frameworks.add(fw)
                break
    return sorted(frameworks)


def detect_tools(root: Path) -> List[str]:
    tools = []
    if (root / "Dockerfile").exists() or list(root.rglob("Dockerfile")):
        tools.append("docker")
    if (root / "docker-compose.yml").exists() or (
        root / "docker-compose.yaml"
    ).exists():
        tools.append("docker_compose")
    if (root / ".github" / "workflows").exists():
        tools.append("github_actions")
    if (root / ".gitlab-ci.yml").exists():
        tools.append("gitlab_ci")
    if (root / "Jenkinsfile").exists():
        tools.append("jenkins")
    if (root / ".circleci" / "config.yml").exists():
        tools.append("circleci")
    if (root / "Makefile").exists():
        tools.append("make")
    if (root / "Justfile").exists() or (root / "justfile").exists():
        tools.append("just")
    if (root / ".editorconfig").exists():
        tools.append("editorconfig")
    if (root / ".pre-commit-config.yaml").exists():
        tools.append("pre_commit")
    if (root / "Daggerfile").exists() or (root / "dagger.json").exists():
        tools.append("dagger")
    if list(root.rglob("*.tf")):
        tools.append("terraform")
    if list(root.rglob("*.ps1")):
        tools.append("powershell")
    if (root / ".devcontainer" / "devcontainer.json").exists():
        tools.append("devcontainer")
    if (root / ".vscode" / "extensions.json").exists():
        tools.append("vscode_workspace")
    if (root / ".mise.toml").exists() or (root / ".mise" / "config.toml").exists():
        tools.append("mise")
    if (root / "uv.lock").exists():
        tools.append("uv")
    if (root / "pnpm-lock.yaml").exists():
        tools.append("pnpm")
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        tools.append("bun")
    return sorted(tools)


def detect_gaps(
    root: Path, components: List[Dict], ecosystems: List[str], tools: List[str]
) -> List[Dict]:
    gaps = []
    test_dirs = {"tests", "test", "__tests__", "spec", "specs", "e2e", "cypress"}
    has_test_dir = any((root / d).exists() for d in test_dirs)
    has_test_files = bool(
        list(root.rglob("test_*.py"))
        or list(root.rglob("*_test.py"))
        or list(root.rglob("*.test.ts"))
        or list(root.rglob("*.spec.ts"))
        or list(root.rglob("*.test.js"))
        or list(root.rglob("*.spec.js"))
        or list(root.rglob("*_test.rs"))
        or list(root.rglob("*_test.go"))
    )
    has_test_dep = any(
        c["name"].lower()
        in ("pytest", "jest", "vitest", "mocha", "junit", "rspec", "ginkgo")
        for c in components
    )
    if not has_test_dir and not has_test_files and not has_test_dep:
        gaps.append({"category": "testing", **GAP_DEFINITIONS["testing"]})

    has_ci = (
        "github_actions" in tools
        or "gitlab_ci" in tools
        or "jenkins" in tools
        or "circleci" in tools
    )
    if not has_ci:
        gaps.append({"category": "ci_cd", **GAP_DEFINITIONS["ci_cd"]})

    has_docker = "docker" in tools
    if not has_docker and ecosystems:
        gaps.append({"category": "docker", **GAP_DEFINITIONS["docker"]})

    if not (root / "README.md").exists():
        gaps.append({"category": "readme", **GAP_DEFINITIONS["readme"]})

    has_license = any(
        (root / name).exists()
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
    )
    if not has_license:
        gaps.append({"category": "license", **GAP_DEFINITIONS["license"]})

    lint_configs = {
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.json",
        ".eslintrc.yaml",
        ".flake8",
        "ruff.toml",
        ".ruff.toml",
        "pyproject.toml",
        ".prettierrc",
        ".prettierrc.js",
        ".prettierrc.json",
        ".rubocop.yml",
        ".rubocop.yaml",
        ".golangci.yml",
        ".golangci.yaml",
        "clang-format",
        ".clang-format",
        ".clang-tidy",
    }
    has_lint = any((root / c).exists() for c in lint_configs)
    if not has_lint:
        has_lint_dep = any(
            c["name"].lower()
            in ("ruff", "eslint", "prettier", "black", "flake8", "golangci-lint")
            for c in components
        )
    if not has_lint and not has_lint_dep:
        gaps.append({"category": "linting", **GAP_DEFINITIONS["linting"]})

    if not (root / "SECURITY.md").exists():
        if not any(
            c["name"].lower() in ("bandit", "safety", "semgrep") for c in components
        ):
            gaps.append({"category": "security", **GAP_DEFINITIONS["security"]})

    if not (root / "CHANGELOG.md").exists():
        gaps.append({"category": "changelog", **GAP_DEFINITIONS["changelog"]})

    if not (root / "CONTRIBUTING.md").exists():
        gaps.append({"category": "contributing", **GAP_DEFINITIONS["contributing"]})

    if not (root / ".github" / "CODEOWNERS").exists():
        gaps.append({"category": "codeowners", **GAP_DEFINITIONS["codeowners"]})

    if (
        not has_docker
        and not (root / "docker-compose.yml").exists()
        and not (root / "docker-compose.yaml").exists()
    ):
        if "docker" not in tools:
            gaps.append(
                {"category": "docker_compose", **GAP_DEFINITIONS["docker_compose"]}
            )

    if not (root / ".env.example").exists() and not (root / ".env.template").exists():
        gaps.append({"category": "env_example", **GAP_DEFINITIONS["env_example"]})

    if "make" not in tools:
        gaps.append({"category": "makefile", **GAP_DEFINITIONS["makefile"]})

    return gaps


def calculate_health(components: List[Dict], gaps: List[Dict], languages: Dict) -> Dict:
    total = len(components)
    high_count = sum(1 for g in gaps if g.get("severity") == "high")
    medium_count = sum(1 for g in gaps if g.get("severity") == "medium")
    low_count = sum(1 for g in gaps if g.get("severity") == "low")
    total_langs = len(languages)
    lang_score = min(20, total_langs * 5)

    coverage = max(
        0,
        min(
            100,
            20
            + lang_score
            + max(0, 30 - high_count * 15)
            + max(0, 30 - medium_count * 10)
            + max(0, 20 - low_count * 5)
            + min(15, total * 0.5),
        ),
    )
    return {
        "totalComponents": total,
        "coverage": round(coverage, 1),
        "highGaps": high_count,
        "mediumGaps": medium_count,
        "lowGaps": low_count,
        "detectedLanguages": total_langs,
    }


def merge_cdxgen_components(
    manual: List[Dict], cdxgen_data: Optional[Dict]
) -> List[Dict]:
    if cdxgen_data is None:
        return manual
    try:
        seen = {(c["name"], c["ecosystem"]) for c in manual}
        for comp in cdxgen_data.get("components", []):
            name = comp.get("name", "")
            if not name:
                continue
            eco_map = {
                "npm": "npm",
                "pypi": "pip",
                "cargo": "cargo",
                "golang": "go",
                "maven": "maven",
                "gem": "gem",
                "composer": "packagist",
                "nuget": "nuget",
            }
            eco = eco_map.get(comp.get("type", "").lower(), comp.get("type", "unknown"))
            version = comp.get("version", "latest")
            if isinstance(version, dict):
                version = version.get("name", "latest")
            if (name, eco) not in seen:
                seen.add((name, eco))
                manual.append(
                    {
                        "name": name,
                        "version": str(version) if version else "latest",
                        "ecosystem": eco,
                        "type": "direct",
                    }
                )
    except Exception:
        pass
    return manual


def scan_inventory(path: str) -> Dict[str, Any]:
    root = Path(path).resolve()
    name = root.name

    ecosystems = detect_ecosystems(root)

    components = []

    if "node" in ecosystems:
        components.extend(parse_package_json(root / "package.json"))

    if "python" in ecosystems:
        components.extend(parse_requirements_txt(root / "requirements.txt"))
        components.extend(parse_pyproject_toml(root / "pyproject.toml"))
        components.extend(parse_setup_cfg(root / "setup.cfg"))

    if "rust" in ecosystems:
        components.extend(parse_cargo_toml(root / "Cargo.toml"))

    if "go" in ecosystems:
        components.extend(parse_go_mod(root / "go.mod"))

    if "java" in ecosystems:
        pom = root / "pom.xml"
        if pom.exists():
            components.extend(parse_pom_xml(pom))

    if "ruby" in ecosystems:
        gf = root / "Gemfile"
        if gf.exists():
            components.extend(parse_gemfile(gf))

    if "php" in ecosystems:
        cf = root / "composer.json"
        if cf.exists():
            components.extend(parse_composer_json(cf))

    cdxgen_data = try_cdxgen(root)
    components = merge_cdxgen_components(components, cdxgen_data)

    cve_data = try_grype(root)

    cloc_data = try_cloc(root)
    if cloc_data and isinstance(cloc_data, dict):
        languages = {}
        for lang, stats in cloc_data.items():
            if lang in ("header", "SUM"):
                continue
            if isinstance(stats, dict) and "nFiles" in stats:
                languages[lang.lower()] = {
                    "files": stats["nFiles"],
                    "loc": stats["code"],
                }
    else:
        languages = analyze_files(root)

    frameworks = detect_frameworks(components)
    tools = detect_tools(root)
    gaps = detect_gaps(root, components, ecosystems, tools)

    if cve_data:
        vulns = cve_data.get("matches", [])
        high_vulns = sum(
            1
            for v in vulns
            if v.get("vulnerability", {}).get("severity", "").lower() == "high"
        )
        crit_vulns = sum(
            1
            for v in vulns
            if v.get("vulnerability", {}).get("severity", "").lower() == "critical"
        )
        if crit_vulns > 0 or high_vulns > 3:
            gaps.append(
                {
                    "category": "vulnerabilities",
                    "severity": "high",
                    "detail": f"Found {crit_vulns} critical and {high_vulns} high severity vulnerabilities",
                    "recommendation": "Run 'grype dir:. -o json' for full report and update affected dependencies",
                }
            )
        elif high_vulns > 0:
            gaps.append(
                {
                    "category": "vulnerabilities",
                    "severity": "medium",
                    "detail": f"Found {high_vulns} high severity vulnerabilities",
                    "recommendation": "Review and update affected dependencies",
                }
            )

    health = calculate_health(components, gaps, languages)

    result = {
        "name": name,
        "ecosystems": ecosystems,
        "components": components,
        "radar": {
            "languages": languages,
            "frameworks": frameworks,
            "tools_detected": tools,
        },
        "gaps": gaps,
        "health": health,
    }

    if cdxgen_data:
        result["_sbom"] = {
            "generated": True,
            "tool": "cdxgen",
            "format": cdxgen_data.get("bomFormat", "CycloneDX"),
            "version": cdxgen_data.get("specVersion", "unknown"),
        }
    if cve_data:
        result["_vulnerabilities"] = {
            "scanned": True,
            "tool": "grype",
            "total": len(cve_data.get("matches", [])),
            "critical": sum(
                1
                for v in cve_data.get("matches", [])
                if v.get("vulnerability", {}).get("severity", "").lower() == "critical"
            ),
            "high": sum(
                1
                for v in cve_data.get("matches", [])
                if v.get("vulnerability", {}).get("severity", "").lower() == "high"
            ),
            "medium": sum(
                1
                for v in cve_data.get("matches", [])
                if v.get("vulnerability", {}).get("severity", "").lower() == "medium"
            ),
        }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="IAS Inventory — Local Stack SBOM, Technology Radar, and Gap Analysis"
    )
    parser.add_argument("path", type=str, help="Project directory to scan")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", type=str, help="Write JSON output to file")

    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)
    if not target.is_dir():
        print(f"Error: Path is not a directory: {args.path}", file=sys.stderr)
        sys.exit(1)

    result = scan_inventory(str(target))

    if args.json:
        output_json = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output_json, encoding="utf-8")
        else:
            print(output_json)
    else:
        radar = result.get("radar", {})
        gaps = result.get("gaps", [])
        health = result.get("health", {})
        langs = radar.get("languages", {})
        frameworks = radar.get("frameworks", [])

        print(f"\n{'=' * 60}")
        print(f"  IAS Inventory Report: {result['name']}")
        print(f"{'=' * 60}")
        print(
            f"\n  Ecosystems: {', '.join(result['ecosystems']) if result['ecosystems'] else 'none detected'}"
        )
        print(f"  Components: {len(result['components'])}")
        print(f"  Languages:  {len(langs)}")
        print(
            f"  Frameworks: {', '.join(frameworks) if frameworks else 'none detected'}"
        )

        print(f"\n  {'LANGUAGE':<15} {'FILES':>8} {'LOC':>10}")
        print(f"  {'-' * 33}")
        for lang in sorted(langs.keys()):
            info = langs[lang]
            print(f"  {lang:<15} {info['files']:>8} {info['loc']:>10}")

        if frameworks:
            print(f"\n  Frameworks: {', '.join(frameworks)}")
        tools = radar.get("tools_detected", [])
        if tools:
            print(f"  Tools: {', '.join(tools)}")

        if gaps:
            print(f"\n  {'GAPS DETECTED':^60}")
            print(f"  {'-' * 60}")
            for g in gaps:
                sev = g.get("severity", "?")
                icon = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}.get(
                    sev, "[?]"
                )
                print(f"  {icon} {g.get('category', '?')}: {g.get('detail', '')}")
                print(f"       -> {g.get('recommendation', '')}")

        print(f"\n  {'HEALTH':^60}")
        print(f"  {'-' * 60}")
        print(f"  Coverage:       {health.get('coverage', 0)}%")
        print(f"  Components:     {health.get('totalComponents', 0)}")
        print(f"  High Gaps:      {health.get('highGaps', 0)}")
        print(f"  Medium Gaps:    {health.get('mediumGaps', 0)}")
        print(f"  Low Gaps:       {health.get('lowGaps', 0)}")
        if result.get("_sbom"):
            print(f"  SBOM:           Generated via cdxgen")
        if result.get("_vulnerabilities"):
            vuln = result["_vulnerabilities"]
            print(
                f"  Vulnerabilities: {vuln.get('total', 0)} total "
                f"({vuln.get('critical', 0)} critical, {vuln.get('high', 0)} high)"
            )
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
