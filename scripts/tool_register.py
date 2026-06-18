#!/usr/bin/env python3
"""
tool_register.py — Kwatermistrz: Rejestracja narzędzia dla /tool-use.

Auto-detekcja metadanych (package.json, pyproject.toml, etc.)
Odczyt .planCS dla lokalizacji instalacji
Odczyt .envy dla portów i konfiguracji
Rejestracja w data/tool_registry.json
LanceDB upsert (embedding opisu)
Generowanie quick_start.md

Użycie:
  python tool_register.py R:/Dev/Tools/Remotion
  python tool_register.py --list
  python tool_register.py --list --domain video
  python tool_register.py --quick R:/Dev/Tools/Remotion
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

IAS_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = IAS_ROOT / "data" / "tool_registry.json"
PLANCS_PATH = IAS_ROOT / "backend" / ".planCS"
ENVY_PATH = IAS_ROOT / "backend" / ".envy"
QUICK_START_DIR = IAS_ROOT.parent.parent / "Vaults" / "tool-registry" / "quick_start"


# ──────────────────────────────────────────────────────────────
# PARSING .planCS i .envy
# ──────────────────────────────────────────────────────────────


def parse_ini_file(path: Path) -> Dict[str, Dict[str, str]]:
    """Parsuje plik INI-like (.planCS, .envy) do zagnieżdżonego dict."""
    config = {}
    current_section = "default"
    if not path.exists():
        return config
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].lower()
            config[current_section] = {}
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            config.setdefault(current_section, {})[key.strip()] = val.strip()
    return config


def get_install_location(tool_type: str, tool_name: str) -> str:
    """Na podstawie .planCS decyduje gdzie zainstalować narzędzie."""
    plancs = parse_ini_file(PLANCS_PATH)
    dirs_map = plancs.get("directories_map", {})

    # Mapowanie typu narzędzia na katalog z .planCS
    type_to_dir = {
        "cli": dirs_map.get("DEVELOPER_TOOLS", r"R:\Dev\Tools"),
        "python": dirs_map.get("MODULES_DIR", r"R:\Dev\Tools"),
        "plugin": dirs_map.get(
            "BACKEND_ROOT", r"C:\Users\13ty\.config\opencode\plugins"
        ),
        "jar": dirs_map.get("DEVELOPER_TOOLS", r"R:\Dev\Tools"),
        "repo": dirs_map.get("MODULES_DIR", r"R:\Dev\Tools"),
    }
    base = type_to_dir.get(tool_type, r"R:\Dev\Tools")
    return os.path.join(base, tool_name)


def get_used_ports() -> List[int]:
    """Zwraca listę zajętych portów z .envy."""
    envy = parse_ini_file(ENVY_PATH)
    ext = envy.get("external_dependencies", {})
    ports = []
    for key, val in ext.items():
        if "port" in key.lower():
            try:
                ports.append(int(val))
            except ValueError:
                pass
    return ports


# ──────────────────────────────────────────────────────────────
# AUTO-DETEKCJA METADANYCH
# ──────────────────────────────────────────────────────────────


def detect_tool_type(path: Path) -> str:
    """Auto-detekcja typu narzędzia na podstawie zawartości."""
    if (path / "package.json").exists():
        return "cli"
    if (
        (path / "pyproject.toml").exists()
        or (path / "requirements.txt").exists()
        or (path / "setup.py").exists()
    ):
        return "python"
    if list(path.glob("*.jar")):
        return "jar"
    if (path / ".git").exists() or (path / ".gitignore").exists():
        return "repo"
    if (path / "plugin.json").exists() or (path / "SKILL.md").exists():
        return "plugin"
    return "cli"


def detect_version(path: Path, tool_type: str) -> str:
    """Auto-detekcja wersji."""
    if tool_type == "cli" and (path / "package.json").exists():
        try:
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
            return pkg.get("version", "unknown")
        except Exception:
            pass
    if tool_type == "python":
        for f in ["pyproject.toml", "setup.py"]:
            if (path / f).exists():
                content = (path / f).read_text(encoding="utf-8")
                m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if m:
                    return m.group(1)
    # Fallback: git describe
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=str(path),
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().lstrip("v")
    except Exception:
        pass
    return "0.1.0"


def detect_name(path: Path) -> str:
    """Auto-detekcja nazwy narzędzia."""
    if (path / "package.json").exists():
        try:
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
            return pkg.get("name", path.name)
        except Exception:
            pass
    if (path / "pyproject.toml").exists():
        content = (path / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            return m.group(1)
    return path.name


def detect_description(path: Path) -> str:
    """Auto-detekcja opisu z README lub package.json."""
    # package.json
    if (path / "package.json").exists():
        try:
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
            desc = pkg.get("description", "")
            if desc:
                return desc
        except Exception:
            pass
    # README
    for readme in path.glob("README*"):
        if readme.is_file():
            content = readme.read_text(encoding="utf-8", errors="ignore")
            first_lines = content.split("\n")[:10]
            for line in first_lines:
                line = line.strip().lstrip("#").strip()
                if line and len(line) > 10:
                    return line
    return ""


def detect_run_command(path: Path, tool_type: str, name: str) -> str:
    """Auto-detekcja komendy uruchomienia."""
    if tool_type == "python" and (path / "pyproject.toml").exists():
        return f"cd {path} && uv run {name}"
    if tool_type == "cli" and (path / "package.json").exists():
        pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        if scripts:
            first_script = list(scripts.keys())[0]
            return f"cd {path} && npm run {first_script}"
    if tool_type == "jar":
        jar_files = list(path.glob("*.jar"))
        if jar_files:
            return f"java -jar {jar_files[0]}"
    return f"cd {path} && {name}"


def detect_domain(path: Path, name: str, description: str) -> str:
    """Heurystyka domeny na podstawie nazwy i opisu."""
    text = f"{name} {description}".lower()
    domain_keywords = {
        "visual": [
            "diagram",
            "chart",
            "graph",
            "draw",
            "mermaid",
            "plantuml",
            "svg",
            "canvas",
        ],
        "code-analysis": [
            "parse",
            "lint",
            "analyze",
            "ast",
            "syntax",
            "tree-sitter",
            "semgrep",
        ],
        "data": [
            "database",
            "sql",
            "query",
            "analytics",
            "csv",
            "json",
            "duckdb",
            "notebook",
        ],
        "dev": ["find", "search", "grep", "file", "voice", "hotkey", "terminal"],
        "devops": ["docker", "ci", "cd", "pipeline", "deploy", "kubernetes", "action"],
        "ai": ["llm", "prompt", "model", "embedding", "rag", "agent", "ml"],
        "video": ["video", "ffmpeg", "animation", "render", "motion"],
        "testing": ["test", "spec", "assert", "mock", "coverage"],
        "security": ["security", "scan", "vulnerability", "audit", "sast"],
    }
    for domain, keywords in domain_keywords.items():
        if any(kw in text for kw in keywords):
            return domain
    return "dev"


# ──────────────────────────────────────────────────────────────
# REJESTRACJA
# ──────────────────────────────────────────────────────────────


def load_registry() -> Dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"version": "2.0.0", "tools": {}, "domains": {}}


def save_registry(registry: Dict) -> None:
    registry["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def register_tool(path: str, quick: bool = False) -> Dict:
    """Główna funkcja rejestracji narzędzia."""
    tool_path = Path(path).resolve()
    if not tool_path.exists():
        print(f"❌ Ścieżka nie istnieje: {path}")
        sys.exit(1)

    # 1. Auto-detekcja
    tool_type = detect_tool_type(tool_path)
    name = detect_name(tool_path)
    version = detect_version(tool_path, tool_type)
    description = detect_description(tool_path)
    domain = detect_domain(tool_path, name, description)
    run_cmd = detect_run_command(tool_path, tool_type, name)
    install_location = get_install_location(tool_type, name)

    print(f"📦 Rejestracja: {name}")
    print(f"   Typ: {tool_type} | Wersja: {version} | Domena: {domain}")
    print(f"   Opis: {description[:100]}")
    print(f"   Run: {run_cmd}")
    print(f"   Install: {install_location}")

    # 2. Sprawdź duplikaty
    registry = load_registry()
    existing = {tid.lower(): tid for tid in registry.get("tools", {})}
    if name.lower() in existing:
        print(f"⚠️  Narzędzie już istnieje: {existing[name.lower()]}")
        return registry["tools"][existing[name.lower()]]

    # 3. Zbuduj rekord
    tool_id = name
    tool_data = {
        "name": name,
        "version": version,
        "type": tool_type,
        "domain": domain,
        "priority": "hot",
        "status": "active",
        "location": str(install_location),
        "run_command": run_cmd,
        "update_command": f"cd {install_location} && git pull"
        if tool_type == "repo"
        else "",
        "alternatives": [],
        "description": description,
    }

    # 4. Zapisz do registry
    registry["tools"][tool_id] = tool_data
    registry.setdefault("domains", {}).setdefault(domain, []).append(tool_id)
    save_registry(registry)
    print(f"✅ Zarejestrowano w tool_registry.json")

    # 5. LanceDB upsert (jeśli nie --quick)
    if not quick:
        print("   🔄 LanceDB upsert...")
        try:
            from lancedb_upsert import upsert_tool

            lancedb_record = {**tool_data, "tool_id": tool_id}
            ok = upsert_tool(lancedb_record)
            if ok:
                print("   ✅ LanceDB upsert OK")
            else:
                print("   ⚠️  LanceDB upsert failed (kontynuuję)")
        except ImportError:
            print("   ⚠️  lancedb_upsert nie dostępny (pip install lancedb)")
        except Exception as e:
            print(f"   ⚠️  LanceDB error: {e}")

    # 6. Generuj quick_start.md + zapisz do vault
    generate_quick_start(tool_data)

    # 7. Zapisz rejestrację do Obsidian vault
    try:
        from vault_writer import write_tool_registration

        vault_path = write_tool_registration(tool_data)
        print(f"   📝 vault: {vault_path}")
    except ImportError:
        pass
    except Exception as e:
        print(f"   ⚠️  Vault writer error: {e}")

    return tool_data


def generate_quick_start(tool_data: Dict) -> None:
    """Generuje plik quick_start.md dla narzędzia."""
    QUICK_START_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", tool_data["name"].lower())
    path = QUICK_START_DIR / f"{slug}.md"

    content = f"""# {tool_data["name"]}

**Wersja**: {tool_data["version"]}
**Typ**: {tool_data["type"]}
**Domena**: {tool_data["domain"]}
**Lokalizacja**: {tool_data["location"]}

## Uruchomienie

```bash
{tool_data["run_command"]}
```

## Aktualizacja

```bash
{tool_data["update_command"] or "# Brak komendy aktualizacji"}
```

## Opis

{tool_data["description"]}

## Alternatywy

{", ".join(tool_data.get("alternatives", ["brak"]))}

---
*Wygenerowano przez IAS Kwatermistrz ({datetime.now().strftime("%Y-%m-%d")})*
"""
    path.write_text(content, encoding="utf-8")
    print(f"   📝 quick_start: {path}")


def list_tools(domain: Optional[str] = None, priority: Optional[str] = None) -> None:
    """Lista zarejestrowanych narzędzi."""
    registry = load_registry()
    tools = registry.get("tools", {})

    filtered = tools
    if domain:
        filtered = {k: v for k, v in filtered.items() if v.get("domain") == domain}
    if priority:
        filtered = {k: v for k, v in filtered.items() if v.get("priority") == priority}

    if not filtered:
        print("📭 Brak narzędzi w rejestrze")
        return

    print(f"\n📋 Rejestr narzędzi ({len(filtered)}/{len(tools)}):\n")
    print(f"{'NAZWA':<20} {'WERSJA':<12} {'TYP':<12} {'DOMENA':<15} {'STATUS':<10}")
    print("-" * 70)
    for name, data in sorted(filtered.items()):
        print(
            f"{name:<20} {data.get('version', '?'):<12} {data.get('type', '?'):<12} {data.get('domain', '?'):<15} {data.get('status', '?'):<10}"
        )
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="IAS Tool Register")
    parser.add_argument("path", nargs="?", help="Ścieżka do narzędzia")
    parser.add_argument(
        "--quick", action="store_true", help="Szybka rejestracja (bez LanceDB)"
    )
    parser.add_argument("--list", action="store_true", help="Lista narzędzi")
    parser.add_argument("--domain", type=str, help="Filtruj po domenie")
    parser.add_argument(
        "--priority", type=str, help="Filtruj po priorytecie (hot/warm/cold)"
    )
    args = parser.parse_args()

    if args.list:
        list_tools(args.domain, args.priority)
    elif args.path:
        register_tool(args.path, args.quick)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
