#!/usr/bin/env python3
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = frozenset(
    {
        "node_modules",
        ".venv",
        "__pycache__",
        ".git",
        "venv",
        "env",
        "dist",
        "build",
        ".eggs",
        "eggs",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".next",
        ".svelte-kit",
        "coverage",
        ".nuxt",
        ".output",
        "target",
        "bin",
        "obj",
    }
)

CODE_EXTS = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".kt",
        ".kts",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".scala",
        ".vue",
        ".svelte",
        ".ex",
        ".exs",
        ".elm",
        ".clj",
        ".cljs",
        ".cljc",
        ".erl",
        ".hrl",
    }
)

LAYER_KEYWORDS = {
    "domain": ["domain", "model", "entity", "core"],
    "application": ["application", "app", "usecase", "use_case", "service"],
    "infrastructure": [
        "infrastructure",
        "infra",
        "persistence",
        "repository",
        "db",
        "database",
        "external",
    ],
    "presentation": [
        "api",
        "web",
        "controller",
        "presentation",
        "ui",
        "view",
        "routes",
        "endpoints",
    ],
}

ALLOWED_IMPORTS = {
    "domain": set(),
    "application": {"domain"},
    "infrastructure": {"domain", "application"},
    "presentation": {"application", "domain"},
}


def parse_args():
    p = argparse.ArgumentParser(
        description="IAS Analyzer — Clean Architecture & Maintainability Check"
    )
    p.add_argument("path", help="Repository path or git URL to analyze")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--output", help="Write output JSON to file")
    return p.parse_args()


def repo_name(path: str) -> str:
    if path.startswith(("http://", "https://", "git@")):
        name = path.rstrip("/").split("/")[-1]
        return name[:-4] if name.endswith(".git") else name
    return Path(path).resolve().name


def clone_repo(url: str):
    td = Path(tempfile.mkdtemp(prefix="ias-analyze-"))
    try:
        r = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(td)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            print(f"git clone failed: {r.stderr.strip()}", file=sys.stderr)
            shutil.rmtree(td, ignore_errors=True)
            return url, None
        return str(td), td
    except subprocess.TimeoutExpired:
        print("git clone timed out (120s)", file=sys.stderr)
    except Exception as e:
        print(f"git clone error: {e}", file=sys.stderr)
    shutil.rmtree(td, ignore_errors=True)
    return url, None


def _walk_files(root: Path) -> list[Path]:
    files = []
    if not root.is_dir():
        return files
    try:
        for entry in root.rglob("*"):
            if not entry.is_file() or entry.suffix not in CODE_EXTS:
                continue
            try:
                parts = entry.relative_to(root).parts[:-1]
            except ValueError:
                continue
            if any(p in EXCLUDE_DIRS or p.startswith(".") for p in parts):
                continue
            files.append(entry)
    except (PermissionError, OSError):
        pass
    return files


def _count_loc(files: list[Path]) -> tuple[int, int]:
    raw = 0
    code = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = text.splitlines()
        raw += len(lines)
        for ln in lines:
            s = ln.strip()
            if s and not s.startswith(("#", "//", "/*", "*")):
                code += 1
    return raw, code


def _file_layer(rel: Path) -> str:
    for p in rel.parts:
        for ln, kws in LAYER_KEYWORDS.items():
            if any(kw.lower() in p.lower() for kw in kws):
                return ln
    return "other"


def _detect_layer_dirs(root: Path) -> dict[str, list[str]]:
    dirs: dict[str, list[str]] = {}
    if not root.is_dir():
        return dirs
    try:
        for entry in root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            for ln, kws in LAYER_KEYWORDS.items():
                if entry.name.lower() in kws:
                    dirs.setdefault(ln, []).append(entry.name)
                    break
    except (PermissionError, OSError):
        pass
    return dirs


def _find_python_layer_imports(text: str) -> list[str]:
    modules = []
    for m in re.finditer(r"^from\s+([a-zA-Z_]\w*)", text, re.MULTILINE):
        modules.append(m.group(1).lower())
    for m in re.finditer(r"^import\s+([a-zA-Z_]\w*)", text, re.MULTILINE):
        modules.append(m.group(1).lower())
    return modules


def _find_jsts_imports(text: str) -> list[str]:
    imports = []
    pattern = r"""(?:import\s+(?:.*?\s+)?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))"""
    for m in re.finditer(pattern, text):
        p = m.group(1) or m.group(2) or ""
        imports.append(p)
    return imports


def _check_violations(files: list[Path], root: Path) -> list[str]:
    violations: list[str] = []
    root_str = str(root).lower()
    for f in files:
        try:
            rel = f.relative_to(root)
        except ValueError:
            continue
        fl = _file_layer(rel)
        if fl == "other" or fl not in ALLOWED_IMPORTS:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        allowed = ALLOWED_IMPORTS[fl]
        if f.suffix == ".py":
            modules = _find_python_layer_imports(text)
            for mod in modules:
                for tln, kws in LAYER_KEYWORDS.items():
                    if tln == fl:
                        continue
                    if any(kw == mod for kw in kws):
                        if tln not in allowed:
                            v = f"Layer violation: {fl} imports {tln} in {rel}"
                            if v not in violations:
                                violations.append(v)
                        break
        elif f.suffix in (".js", ".jsx", ".ts", ".tsx"):
            imps = _find_jsts_imports(text)
            for imp in imps:
                imp_lower = imp.lower()
                for tln, kws in LAYER_KEYWORDS.items():
                    if tln == fl:
                        continue
                    if any(
                        f"/{kw}/" in imp_lower
                        or imp_lower.startswith(f"{kw}/")
                        or imp_lower == kw
                        for kw in kws
                    ):
                        if tln not in allowed:
                            v = f"Layer violation: {fl} imports {tln} in {rel}"
                            if v not in violations:
                                violations.append(v)
                        break
    return violations


def _per_file_mi(text: str) -> tuple[float, int]:
    lines = text.splitlines()
    code = sum(
        1
        for ln in lines
        if ln.strip() and not ln.strip().startswith(("#", "//", "/*", "*"))
    )
    loc = max(code, 1)
    cc = len(re.findall(r"\b(?:if|elif|for|while|except|finally|case|switch)\b", text))
    hv = loc * 2.5
    denom = max(float(loc) / max(code, 1), 0.1)
    mi = 171.0 - 5.2 * math.log(max(hv, 1)) - 0.23 * max(cc, 1) - 16.2 * math.log(loc)
    return mi, code


def _calc_maintainability_index(files: list[Path], code_loc: int) -> dict[str, Any]:
    fc = len(files)
    if fc == 0 or code_loc == 0:
        return {"index": 0.0, "rating": "unknown", "loc": 0, "fileCount": 0}
    total_weight = 0
    weighted_mi = 0.0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        mi_file, loc_file = _per_file_mi(text)
        mi_file = max(0.0, min(100.0, mi_file))
        weighted_mi += mi_file * loc_file
        total_weight += loc_file
    mi_avg = weighted_mi / max(total_weight, 1) if total_weight > 0 else 0.0
    if mi_avg >= 85.0:
        rating = "good"
    elif mi_avg >= 65.0:
        rating = "moderate"
    elif mi_avg >= 40.0:
        rating = "poor"
    else:
        rating = "very poor"
    return {
        "index": round(mi_avg, 1),
        "rating": rating,
        "loc": code_loc,
        "fileCount": fc,
    }


def _calc_clean_architecture(
    violations: list[str], layer_dirs: dict[str, list[str]], file_count: int
) -> dict[str, Any]:
    score = 100.0
    penalty = min(len(violations) * 10, 50)
    score -= penalty
    expected = {"domain", "application", "infrastructure"}
    found = set(layer_dirs.keys()) & expected
    missing = expected - found
    score -= len(missing) * 12
    if not found:
        score -= 15
    if file_count == 0:
        score = 0
    score = max(0, min(100, int(round(score))))
    msgs = list(violations)
    for l in sorted(missing):
        msgs.append(f"Missing layer: {l}")
    if not layer_dirs.get("presentation"):
        msgs.append("Missing layer: presentation (optional)")
    return {"score": score, "violationCount": len(violations), "violations": msgs}


def _generate_recs(
    violations: list[str],
    mi: dict[str, Any],
    layer_dirs: dict[str, list[str]],
    code_loc: int,
    file_count: int,
) -> list[str]:
    recs: list[str] = []
    if violations:
        recs.append(f"Resolve {len(violations)} Clean Architecture layer violation(s)")
    if mi.get("rating") in ("poor", "very poor"):
        recs.append(
            "Improve maintainability by reducing complexity, splitting large modules, and adding structure"
        )
    expected = {"domain", "application", "infrastructure"}
    missing = expected - set(layer_dirs.keys())
    if missing:
        recs.append(
            f"Introduce {'/'.join(sorted(missing))} layer(s) for Clean Architecture alignment"
        )
    if file_count > 0 and code_loc / file_count > 500:
        recs.append(
            "Average file size exceeds 500 LOC — split large files into smaller modules"
        )
    if code_loc < 100 and file_count > 0:
        recs.append(
            "Codebase is very small — consider whether Clean Architecture layers are warranted"
        )
    return recs


def main():
    args = parse_args()
    input_path = args.path
    temp_cleanup: Path | None = None
    if input_path.startswith(("http://", "https://", "git@")):
        input_path, temp_cleanup = clone_repo(input_path)
    root = Path(input_path).resolve()
    if not root.exists():
        print(f"Path does not exist: {root}", file=sys.stderr)
        sys.exit(1)
    try:
        files = _walk_files(root)
        _, code_loc = _count_loc(files)
        layer_dirs = _detect_layer_dirs(root)
        violations = _check_violations(files, root)
        mi_result = _calc_maintainability_index(files, code_loc)
        ca_result = _calc_clean_architecture(violations, layer_dirs, len(files))
        recs = _generate_recs(violations, mi_result, layer_dirs, code_loc, len(files))
        result = {
            "name": repo_name(args.path),
            "clean_architecture": ca_result,
            "maintainability": mi_result,
            "recommendations": recs,
        }
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        if args.json:
            print(json.dumps(result, indent=2))
        elif not args.output:
            ca = result["clean_architecture"]
            mi = result["maintainability"]
            print(f"Repository: {result['name']}")
            print(
                f"Clean Architecture: {ca['score']}/100 ({ca['violationCount']} violations)"
            )
            print(f"Maintainability: {mi['index']}/100 ({mi['rating']})")
            print(f"LOC: {mi['loc']} | Files: {mi['fileCount']}")
            if result["recommendations"]:
                print(f"\nRecommendations:")
                for r in result["recommendations"]:
                    print(f"  \u2022 {r}")
    finally:
        if temp_cleanup is not None and temp_cleanup.exists():
            shutil.rmtree(temp_cleanup, ignore_errors=True)


if __name__ == "__main__":
    main()
