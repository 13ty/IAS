#!/usr/bin/env python3
"""
scan_environment.py - Bulk Windows Environment Scanner.

Odkrywa ~2000 instalowalnych narzedzi na Windows developerskiej maszynie
poprzez skanowanie rejestru, PATH, menedzerow pakietow i znanych katalogow.
Wynik: JSON kompatybilny z tool_registry.json (schema v2).

Uzycie:
    python scripts/scan_environment.py                          # pelny skan
    python scripts/scan_environment.py --quick                  # tylko PATH+registry
    python scripts/scan_environment.py --registry-only           # tylko rejestr
    python scripts/scan_environment.py --output data/tools.json  # wlasny output
    python scripts/scan_environment.py --merge                   # merge do tool_registry.json
    python scripts/scan_environment.py --count                   # tylko statystyki
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
import winreg
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

IAS_ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT = IAS_ROOT / "data" / "tool_registry.json"

PROBE_TIMEOUT = 4
PM_TIMEOUT = 30
REGISTRY_TIMEOUT = 15
MAX_WORKERS = 12

REGISTRY_PATHS: List[Tuple[int, str]] = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
]
# Znane katalogi narzedzi
EXE_EXTENSIONS = {'.exe', '.bat', '.cmd', '.ps1', '.com', '.jar'}

IGNORE_NAMES = {
    'conhost', 'cmd', 'powershell', 'pwsh', 'regedit', 'rundll32',
    'svchost', 'ctfmon', 'explorer', 'sihost', 'start', 'runtimebroker',
    'dllhost', 'fontdrvhost', 'lsass', 'services', 'smss',
    'spoolsv', 'system', 'csrss', 'wininit', 'winlogon',
    'shellexperiencehost', 'lockapp', 'searchapp', 'searchui',
    'widgets', 'widgetservice', 'yourphone', 'ntoskrnl', 'hal',
}

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    'visual': ['diagram', 'chart', 'graph', 'draw', 'mermaid', 'plantuml', 'svg', 'canvas', 'ffmpeg', 'remotion'],
    'code-analysis': ['parse', 'lint', 'analyze', 'ast', 'syntax', 'tree-sitter', 'semgrep', 'cloc', 'audit'],
    'data': ['database', 'sql', 'query', 'analytics', 'csv', 'json', 'duckdb', 'notebook', 'parquet'],
    'dev': ['find', 'search', 'grep', 'file', 'voice', 'hotkey', 'terminal', 'ripgrep'],
    'devops': ['docker', 'ci', 'cd', 'pipeline', 'deploy', 'kubernetes', 'action', 'terraform', 'pulumi'],
    'ai': ['llm', 'prompt', 'model', 'embedding', 'rag', 'agent', 'ml', 'openai', 'claude'],
    'testing': ['test', 'spec', 'assert', 'mock', 'coverage', 'vitest', 'pytest'],
    'security': ['security', 'scan', 'vulnerability', 'sast', 'secret', 'gitleaks'],
    'rust': ['cargo', 'rust', 'rustup'],
    'web': ['nginx', 'caddy', 'traefik', 'http', 'server'],
}


@dataclass
class ToolRecord:
    canonical_name: str
    display_name: str
    version: Optional[str] = None
    description: str = ''
    domain: str = 'dev'
    priority: str = 'warm'
    status: str = 'active'
    type: str = 'cli'
    sources: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    @property
    def primary_location(self) -> Optional[str]:
        return self.locations[0] if self.locations else None


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, ToolRecord] = {}
        self._stats = {'total_raw': 0, 'after_dedup': 0, 'by_source': {}, 'by_domain': {}, 'errors': []}

    def add(self, name: str, source: str, location: str = '',
            version: Optional[str] = None, description: str = '',
            domain: str = '', metadata: Optional[Dict] = None) -> str:
        key = self._canonical(name)
        if key in IGNORE_NAMES:
            return key
        self._stats['total_raw'] += 1
        self._stats['by_source'][source] = self._stats['by_source'].get(source, 0) + 1
        if key not in self._tools:
            display, tool_type = self._infer_type(name, location)
            dom = domain or self._infer_domain(name, description, location)
            rec = ToolRecord(
                canonical_name=key, display_name=display, version=version,
                description=description, domain=dom, type=tool_type,
                sources=[source], locations=[location] if location else [],
                metadata=metadata or {},
            )
            if not location and shutil.which(name):
                rec.locations = [shutil.which(name)]
            self._tools[key] = rec
        else:
            rec = self._tools[key]
            if source not in rec.sources:
                rec.sources.append(source)
            if location and location not in rec.locations:
                rec.locations.append(location)
            if version and (not rec.version or len(version) > len(rec.version)):
                rec.version = version
            if description and description not in rec.description:
                rec.description = (rec.description + '; ' + description)[:200]
            if metadata:
                rec.metadata.update(metadata)
        return key

    def get(self, key: str) -> Optional[ToolRecord]:
        return self._tools.get(self._canonical(key))

    @property
    def tools(self) -> Dict[str, ToolRecord]:
        return self._tools

    @property
    def stats(self) -> Dict:
        self._stats['after_dedup'] = len(self._tools)
        self._stats['by_domain'] = {}
        for rec in self._tools.values():
            self._stats['by_domain'][rec.domain] = self._stats['by_domain'].get(rec.domain, 0) + 1
        return self._stats

    @staticmethod
    def _canonical(name: str) -> str:
        n = name.lower().strip()
        for ext in ('.exe', '.bat', '.cmd', '.ps1', '.com', '.jar'):
            if n.endswith(ext):
                n = n[:-len(ext)]
        return re.sub(r'\s+', '-', n).strip('-')

    @staticmethod
    def _infer_type(name: str, location: str):
        p = Path(location) if location else Path(name)
        if location and location.endswith('.jar'):
            return name.replace('.jar', '').replace('-', ' ').strip(), 'jar'
        if 'pipx' in location.lower() or 'python' in location.lower():
            return name.replace('-', ' ').title(), 'python'
        if 'plugin' in location.lower() or 'opencode' in location.lower():
            return name.replace('-', ' ').title(), 'plugin'
        return name.replace('-', ' ').title(), 'cli'

    @staticmethod
    def _infer_domain(name: str, description: str, location: str = '') -> str:
        text = f'{name} {description} {location}'.lower()
        scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[domain] = score
        return max(scores, key=scores.get) if scores else 'dev'

    def merge_into_registry_json(self, registry_path: Path) -> Dict:
        existing = {'version': '2.0.0', 'last_updated': datetime.now().isoformat()[:10], 'tools': {}, 'domains': {}}
        if registry_path.exists():
            try:
                existing = json.loads(registry_path.read_text(encoding='utf-8'))
            except Exception:
                pass
        for rec in self._tools.values():
            key = rec.canonical_name
            if key in existing.get('tools', {}):
                ext = existing['tools'][key]
                if not rec.version and ext.get('version'):
                    rec.version = ext['version']
                if not rec.description and ext.get('description'):
                    rec.description = ext['description']
                if ext.get('priority', 'warm') != 'warm':
                    rec.priority = ext['priority']
                if ext.get('status'):
                    rec.status = ext['status']
            entry = {
                'name': rec.display_name, 'version': rec.version or '',
                'type': rec.type, 'domain': rec.domain,
                'priority': rec.priority, 'status': rec.status,
                'location': rec.primary_location or '',
                'run_command': '', 'update_command': '',
                'alternatives': [], 'description': rec.description,
            }
            if key in existing.get('tools', {}):
                for k, v in existing['tools'][key].items():
                    if k not in entry or not entry[k]:
                        entry[k] = v
            existing.setdefault('tools', {})[key] = entry
        domains: Dict[str, List[str]] = {}
        for key, entry in existing.get('tools', {}).items():
            dom = entry.get('domain', 'dev')
            domains.setdefault(dom, []).append(key)
        existing['domains'] = domains
        existing['last_updated'] = datetime.now().isoformat()[:10]
        return existing

# ──────────────────────────────────────────────
# SAFE VERSION PROBER
# ──────────────────────────────────────────────

def _make_startupinfo():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return si

def probe_version(exe_path: str, timeout: int = PROBE_TIMEOUT) -> Optional[str]:
    flags = ['--version', '-v', '--help']
    for flag in flags:
        try:
            si = _make_startupinfo()
            result = subprocess.run(
                [exe_path, flag], capture_output=True, text=True,
                timeout=timeout, startupinfo=si,
            )
            output = (result.stdout or '').strip() or (result.stderr or '').strip()
            if output:
                for line in output.split('\n'):
                    line = line.strip()
                    if not line or any(x in line.lower() for x in ('error', 'usage', 'not found')):
                        continue
                    if re.search(r'\d+\.\d+', line):
                        return line[:200]
                first = output.split('\n')[0].strip()
                if first:
                    return first[:200]
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError, UnicodeDecodeError):
            continue
    return None

def probe_version_parallel(exe_paths: List[str], max_workers: int = MAX_WORKERS) -> Dict[str, Optional[str]]:
    results: Dict[str, Optional[str]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(probe_version, p): p for p in exe_paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                results[path] = future.result()
            except Exception:
                results[path] = None
    return results


# ──────────────────────────────────────────────
# REGISTRY PROBE
# ──────────────────────────────────────────────

def _reg_val(key, name: str, default=''):
    try:
        val, _ = winreg.QueryValueEx(key, name)
        return val
    except (OSError, FileNotFoundError):
        return default

def _query_registry_key(hive: int, subkey: str) -> List[Dict]:
    apps = []
    try:
        with winreg.OpenKey(hive, subkey) as key:
            count = winreg.QueryInfoKey(key)[0]
            for i in range(count):
                try:
                    with winreg.OpenKey(key, winreg.EnumKey(key, i)) as sk:
                        name = _reg_val(sk, 'DisplayName', '')
                        if not name:
                            continue
                        apps.append({
                            'name': name,
                            'version': _reg_val(sk, 'DisplayVersion', ''),
                            'publisher': _reg_val(sk, 'Publisher', ''),
                            'location': _reg_val(sk, 'InstallLocation', ''),
                            'uninstall': _reg_val(sk, 'UninstallString', ''),
                            'estimated_size': _reg_val(sk, 'EstimatedSize', 0),
                            'install_date': _reg_val(sk, 'InstallDate', ''),
                        })
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError, FileNotFoundError):
        pass
    return apps

def scan_registry() -> List[Dict]:
    seen_names: Set[str] = set()
    results = []
    for hive, path in REGISTRY_PATHS:
        try:
            apps = _query_registry_key(hive, path)
            for app in apps:
                key = app['name'].lower().strip()
                if key and key not in seen_names:
                    seen_names.add(key)
                    results.append(app)
        except Exception:
            continue
    return results

def add_registry_to_registry(reg: ToolRegistry) -> None:
    apps = scan_registry()
    for app in apps:
        location = app.get('location', '') or ''
        reg.add(
            name=app['name'], source='registry', location=location,
            version=app.get('version') or None,
            description=app.get('publisher', '') + ' ' + app.get('name', ''),
            metadata={'install_date': app.get('install_date', ''), 'publisher': app.get('publisher', '')},
        )


# ──────────────────────────────────────────────
# PATH SCANNER
# ──────────────────────────────────────────────

def get_path_dirs() -> List[str]:
    seen: Set[str] = set()
    dirs = []
    for p in os.environ.get('PATH', '').split(';'):
        p = p.strip().strip('"')
        if not p or p.lower() in seen:
            continue
        seen.add(p.lower())
        resolved = os.path.expandvars(p)
        if os.path.isdir(resolved):
            dirs.append(resolved)
    return dirs

def scan_path(reg: ToolRegistry) -> int:
    dirs = get_path_dirs()
    exes: List[str] = []
    seen_names: Set[str] = set()
    for d in dirs:
        try:
            for f in os.listdir(d):
                fpath = os.path.join(d, f)
                if not os.path.isfile(fpath):
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext not in EXE_EXTENSIONS:
                    continue
                name = os.path.splitext(f)[0].lower()
                if name in seen_names or name in IGNORE_NAMES:
                    continue
                seen_names.add(name)
                exes.append(fpath)
        except (PermissionError, OSError):
            continue
    versions = probe_version_parallel(exes)
    for exe_path in exes:
        name = os.path.splitext(os.path.basename(exe_path))[0]
        ver = versions.get(exe_path)
        reg.add(name=name, source='path', location=exe_path, version=ver)
    return len(exes)


# ──────────────────────────────────────────────
# KNOWN DIRECTORIES SCANNER
# ──────────────────────────────────────────────

KNOWN_TOOL_DIRS = [
    r'R:\Dev\Tools',
    r'C:\Program Files',
    r'C:\Program Files (x86)',
    r'C:\Tools',
    r'C:\Utils',
    os.path.expandvars(r'%LOCALAPPDATA%\Programs'),
    os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WindowsApps'),
    os.path.expandvars(r'%APPDATA%\npm'),
    os.path.expandvars(r'%APPDATA%\pnpm'),
    os.path.expandvars(r'%USERPROFILE%\.cargo\bin'),
    os.path.expandvars(r'%USERPROFILE%\.bun\bin'),
    os.path.expandvars(r'%USERPROFILE%\.local\bin'),
    os.path.expandvars(r'%LOCALAPPDATA%\pipx\.venvs'),
    os.path.expandvars(r'%USERPROFILE%\scoop\apps'),
    os.path.expandvars(r'%USERPROFILE%\scoop\shims'),
    os.path.expandvars(r'%USERPROFILE%\scoop\current\bin'),
    os.path.expandvars(r'%ChocolateyInstall%\bin'),
]

def resolve_known_dirs() -> List[str]:
    resolved = []
    for d in KNOWN_TOOL_DIRS:
        try:
            r = os.path.expandvars(d)
            if os.path.isdir(r):
                resolved.append(r)
        except Exception:
            continue
    return resolved

def scan_known_dirs(reg: ToolRegistry) -> int:
    dirs = resolve_known_dirs()
    path_dirs = {d.lower().rstrip('\\\\') for d in get_path_dirs()}
    extra_dirs = [d for d in dirs if d.lower().rstrip('\\\\') not in path_dirs]
    exes: List[str] = []
    seen_names: Set[str] = set()
    for d in extra_dirs:
        try:
            for entry in os.listdir(d):
                fpath = os.path.join(d, entry)
                if os.path.isfile(fpath):
                    ext = os.path.splitext(entry)[1].lower()
                    if ext not in EXE_EXTENSIONS:
                        continue
                    name = os.path.splitext(entry)[0].lower()
                    if name in seen_names or name in IGNORE_NAMES:
                        continue
                    seen_names.add(name)
                    exes.append(fpath)
        except (PermissionError, OSError):
            continue
    versions = probe_version_parallel(exes)
    for exe_path in exes:
        name = os.path.splitext(os.path.basename(exe_path))[0]
        ver = versions.get(exe_path)
        reg.add(name=name, source='known-dir', location=exe_path, version=ver)
    return len(exes)


# ──────────────────────────────────────────────
# PACKAGE MANAGER SCANNERS
# ──────────────────────────────────────────────

def _run_cmd(cmd: List[str], timeout: int = PM_TIMEOUT) -> Optional[str]:
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=si)
        return (result.stdout or '') if result.returncode == 0 else (result.stderr or '')[:500]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None

def _which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def scan_scoop(reg: ToolRegistry) -> int:
    count = 0
    scoop_apps = Path.home() / 'scoop' / 'apps'
    if scoop_apps.is_dir():
        for app_dir in scoop_apps.iterdir():
            if not app_dir.is_dir() or app_dir.name.startswith('.'):
                continue
            current = app_dir / 'current'
            version = None
            if current.is_dir() or current.is_symlink():
                try:
                    version = os.path.basename(os.path.realpath(str(current)))
                except Exception:
                    pass
            reg.add(name=app_dir.name, source='scoop', location=str(app_dir), version=version)
            count += 1
    return count


def scan_winget(reg: ToolRegistry) -> int:
    if not _which('winget'):
        return 0
    output = _run_cmd(['winget', 'list', '--accept-source-agreements'])
    if not output:
        return 0
    count = 0
    for line in output.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].lower() not in ('name', '---') and not parts[0].startswith('-'):
            reg.add(name=parts[0], source='winget', version=parts[1] if len(parts) > 1 else None)
            count += 1
    return count


def scan_choco(reg: ToolRegistry) -> int:
    if not _which('choco'):
        return 0
    output = _run_cmd(['choco', 'list', '-r', '--local-only'])
    if not output:
        return 0
    count = 0
    for line in output.split('\n'):
        line = line.strip()
        if '|' in line:
            parts = line.split('|')
            name = parts[0].strip()
            if name.lower() != 'chocolatey':
                reg.add(name=name, source='choco', version=parts[1].strip() if len(parts) > 1 else None)
                count += 1
    return count


def scan_pipx(reg: ToolRegistry) -> int:
    if not _which('pipx'):
        return 0
    output = _run_cmd(['pipx', 'list', '--json'])
    if not output:
        return 0
    count = 0
    try:
        data = json.loads(output)
        for venv_name, venv_data in data.get('venvs', {}).items():
            main_pkg = venv_data.get('metadata', {}).get('main_package', {})
            name = main_pkg.get('package', venv_name)
            version = main_pkg.get('version')
            apps = main_pkg.get('apps', [])
            location = apps[0] if apps else ''
            reg.add(name=name, source='pipx', location=location, version=version)
            count += 1
    except (json.JSONDecodeError, AttributeError):
        pass
    return count


def scan_cargo(reg: ToolRegistry) -> int:
    if not _which('cargo'):
        return 0
    output = _run_cmd(['cargo', 'install', '--list'])
    if not output:
        return 0
    count = 0
    for line in output.split('\n'):
        line = line.strip()
        if ' ' in line and line[0].isalnum():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0].rstrip(':')
                version = parts[1].lstrip('v')
                reg.add(name=name, source='cargo', version=version,
                        location=str(Path.home() / '.cargo' / 'bin' / f'{name}.exe'))
                count += 1
    return count


def scan_npm(reg: ToolRegistry) -> int:
    if not _which('npm'):
        return 0
    output = _run_cmd(['npm', 'ls', '-g', '--depth=0', '--json'])
    if not output:
        return 0
    count = 0
    try:
        data = json.loads(output)
        for name, info in data.get('dependencies', {}).items():
            version = info.get('version')
            reg.add(name=name, source='npm', version=version,
                    location=str(Path(os.environ.get('APPDATA', '')) / 'npm' / 'node_modules' / name))
            count += 1
    except (json.JSONDecodeError, AttributeError):
        pass
    return count


def scan_bun(reg: ToolRegistry) -> int:
    if not _which('bun'):
        return 0
    count = 0
    bun_global = Path.home() / '.bun' / 'install' / 'global' / 'node_modules'
    if bun_global.is_dir():
        for pkg_dir in bun_global.iterdir():
            if not pkg_dir.is_dir() or pkg_dir.name.startswith('.') or pkg_dir.name.startswith('@'):
                continue
            pkg_json = pkg_dir / 'package.json'
            version = None
            if pkg_json.exists():
                try:
                    data = json.loads(pkg_json.read_text(encoding='utf-8'))
                    version = data.get('version')
                except Exception:
                    pass
            reg.add(name=pkg_dir.name, source='bun', version=version, location=str(pkg_dir))
            count += 1
    return count


def scan_dotnet_tools(reg: ToolRegistry) -> int:
    if not _which('dotnet'):
        return 0
    output = _run_cmd(['dotnet', 'tool', 'list', '-g'])
    if not output:
        return 0
    count = 0
    for line in output.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].lower() not in ('package', '---'):
            reg.add(name=parts[0], source='dotnet-tool', version=parts[1] if len(parts) > 1 else None)
            count += 1
    return count


def scan_pnpm(reg: ToolRegistry) -> int:
    if not _which('pnpm'):
        return 0
    output = _run_cmd(['pnpm', 'list', '-g', '--depth=0', '--json'])
    if not output:
        return 0
    count = 0
    try:
        data = json.loads(output)
        items = data if isinstance(data, list) else [data]
        for item in items:
            for name, info in item.get('dependencies', {}).items():
                reg.add(name=name, source='pnpm', version=info.get('version', ''))
                count += 1
    except (json.JSONDecodeError, AttributeError):
        pass
    return count


# ──────────────────────────────────────────────
# R:\Dev\Tools METADATA SCANNER
# ──────────────────────────────────────────────

def scan_dev_tools_dir(reg: ToolRegistry, dev_tools_path: str = r'R:\Dev\Tools') -> int:
    dt = Path(dev_tools_path)
    if not dt.is_dir():
        return 0
    count = 0
    for entry in dt.iterdir():
        if not entry.is_dir() or entry.name.startswith('.'):
            continue
        name = entry.name
        version = None
        description = ''
        domain = ''
        pkg_json = entry / 'package.json'
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding='utf-8', errors='ignore'))
                name = data.get('name', name)
                version = data.get('version', version)
                description = data.get('description', '')
            except Exception:
                pass
        pyproj = entry / 'pyproject.toml'
        if pyproj.exists():
            try:
                content = pyproj.read_text(encoding='utf-8', errors='ignore')
                m = re.search(r'version\s*=\s*["\\'']([^"\\'']+)["\\'']', content)
                if m:
                    version = m.group(1)
                m2 = re.search(r'description\s*=\s*["\\'']([^"\\'']+)["\\'']', content)
                if m2:
                    description = m2.group(1)
            except Exception:
                pass
        if not description:
            for readme in entry.glob('README*'):
                try:
                    lines = readme.read_text(encoding='utf-8', errors='ignore').split('\n')
                    for line in lines[:10]:
                        line = line.strip().lstrip('#').strip()
                        if line and len(line) > 10:
                            description = line
                            break
                except Exception:
                    pass
        reg.add(name=name, source='dev-tools', location=str(entry),
                version=version, description=description, domain=domain)
        count += 1
    return count


# ──────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────

def scan_all(quick: bool = False, registry_only: bool = False, json_report: bool = False) -> ToolRegistry:
    reg = ToolRegistry()
    start = time.time()

    # Faza 1: Registry (szybki, zawsze)
    print('[1/5] Registry scan...', end=' ', flush=True)
    try:
        add_registry_to_registry(reg)
        s = reg.stats
        print(f'{s["after_dedup"]} tools')
    except Exception as e:
        print(f'ERROR: {e}')

    if registry_only:
        print(f'  Done in {time.time()-start:.1f}s')
        return reg

    # Faza 2: PATH (rownolegly)
    print('[2/5] PATH scan (parallel)...', end=' ', flush=True)
    try:
        pc = scan_path(reg)
        print(f'{pc} exes, {len(reg.tools)} cumulative')
    except Exception as e:
        print(f'ERROR: {e}')

    if quick:
        print(f'  Done in {time.time()-start:.1f}s')
        return reg

    # Faza 3: Known directories
    print('[3/5] Known dirs...', end=' ', flush=True)
    try:
        kc = scan_known_dirs(reg)
        print(f'{kc} exes, {len(reg.tools)} cumulative')
    except Exception as e:
        print(f'ERROR: {e}')

    # Faza 4: Package managers (rownolegle)
    pm_scanners = [
        ('scoop', scan_scoop), ('winget', scan_winget), ('choco', scan_choco),
        ('pipx', scan_pipx), ('cargo', scan_cargo), ('npm', scan_npm),
        ('bun', scan_bun), ('dotnet-tool', scan_dotnet_tools), ('pnpm', scan_pnpm),
    ]
    print('[4/5] Package managers (parallel)...')
    pm_start = time.time()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {}
        for pm_name, scanner_fn in pm_scanners:
            futures[pool.submit(scanner_fn, reg)] = pm_name
        for future in as_completed(futures):
            pm_name = futures[future]
            try:
                cnt = future.result()
                print(f'  {pm_name}: {cnt} tools')
            except Exception as e:
                print(f'  {pm_name}: ERROR {e}')
    print(f'  PM total: {time.time()-pm_start:.1f}s')

    # Faza 5: R:\\Dev\\Tools metadata
    print('[5/5] R:\\Dev\\Tools metadata...', end=' ', flush=True)
    try:
        dc = scan_dev_tools_dir(reg)
        print(f'{dc} dirs, {len(reg.tools)} cumulative')
    except Exception as e:
        print(f'ERROR: {e}')

    elapsed = time.time() - start
    stats = reg.stats
    total = stats['after_dedup']
    print(f'\n==== SCAN COMPLETE in {elapsed:.1f}s ====')
    print(f'  Raw entries:  {stats["total_raw"]}')
    print(f'  After dedup:  {total}')
    print(f'  By domain:    {stats["by_domain"]}')
    print(f'  By source:    {stats["by_source"]}')

    if json_report:
        report = {
            'scan_time': elapsed,
            'timestamp': datetime.now().isoformat(),
            'total_raw': stats['total_raw'],
            'total_unique': total,
            'by_source': stats['by_source'],
            'by_domain': stats['by_domain'],
            'sources_used': [pm for pm, _ in pm_scanners if _which(pm.split('-')[0]) or pm == 'scoop']
                           + ['registry', 'path', 'known-dir', 'dev-tools'],
        }
        report_path = IAS_ROOT / 'data' / 'scan_report.json'
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'  Report saved: {report_path}')

    return reg


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Bulk Windows Environment Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python scripts/scan_environment.py
  python scripts/scan_environment.py --quick
  python scripts/scan_environment.py --registry-only
  python scripts/scan_environment.py --output data/tools.json
  python scripts/scan_environment.py --merge
  python scripts/scan_environment.py --count --json
        ''',
    )
    parser.add_argument('--quick', action='store_true', help='Tylko PATH + registry')
    parser.add_argument('--registry-only', action='store_true', help='Tylko rejestr')
    parser.add_argument('--output', default=None, help='Sciezka output JSON')
    parser.add_argument('--merge', action='store_true', help='Merge do tool_registry.json')
    parser.add_argument('--count', action='store_true', help='Tylko statystyki (bez zapisu)')
    parser.add_argument('--json', action='store_true', help='Zapisz raport JSON')

    args = parser.parse_args()

    # Przygotowanie IAS katalogow jesli nie istnieja
    (IAS_ROOT / 'data').mkdir(parents=True, exist_ok=True)

    reg = scan_all(quick=args.quick, registry_only=args.registry_only, json_report=args.json)

    if args.merge:
        output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
        merged = reg.merge_into_registry_json(output_path)
        output_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'\\nMerged {len(reg.tools)} tools into {output_path}')
        print(f'  Total in registry: {len(merged["tools"])} tools')
        print(f'  Domains: {list(merged["domains"].keys())}')

    elif args.output:
        output_path = Path(args.output)
        data = {
            'version': '2.0.0',
            'last_updated': datetime.now().isoformat()[:10],
            'scan_stats': reg.stats,
            'tools': {
                rec.canonical_name: {
                    'name': rec.display_name,
                    'version': rec.version or '',
                    'type': rec.type,
                    'domain': rec.domain,
                    'priority': rec.priority,
                    'status': rec.status,
                    'location': rec.primary_location or '',
                    'sources': rec.sources,
                    'description': rec.description,
                }
                for rec in reg.tools.values()
            },
        }
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'\\nWritten {len(reg.tools)} tools to {output_path}')

    elif args.count:
        print(f'\\nTotal unique tools found: {len(reg.tools)}')
        stats = reg.stats
        for src, cnt in sorted(stats['by_source'].items(), key=lambda x: -x[1]):
            print(f'  {src}: {cnt}')
        print(f'  ---')
        for dom, cnt in sorted(stats['by_domain'].items(), key=lambda x: -x[1]):
            print(f'  {dom}: {cnt}')

    else:
        print(f'\\nFound {len(reg.tools)} unique tools.')
        print('Use --output to save, --merge to update tool_registry.json, or --count for stats.')


if __name__ == '__main__':
    main()
