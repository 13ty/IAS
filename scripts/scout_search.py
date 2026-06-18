#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

GAP_QUERIES = {
    "testing": ["testing framework", "test runner", "testing library", "unit testing"],
    "security": [
        "security scanner",
        "vulnerability detection",
        "security audit tool",
        "dependency security",
    ],
    "documentation": [
        "documentation generator",
        "docs generator",
        "api documentation",
        "mkdocs plugin",
    ],
    "ci-cd": ["ci cd pipeline", "continuous integration", "github actions", "ci tool"],
    "ci/cd": ["ci cd pipeline", "continuous integration", "github actions", "ci tool"],
    "monitoring": [
        "monitoring tool",
        "observability",
        "application monitoring",
        "metrics dashboard",
    ],
    "linting": ["linter", "code quality", "static analysis", "lint tool"],
    "formatting": ["code formatter", "auto formatter", "code style", "prettier"],
    "database": ["orm", "database client", "database migration", "sql toolkit"],
    "logging": ["logging library", "structured logging", "log management"],
    "caching": ["caching library", "cache tool", "distributed cache", "redis client"],
    "containerization": [
        "docker tool",
        "kubernetes",
        "container orchestration",
        "container management",
    ],
    "deployment": [
        "deployment tool",
        "release automation",
        "infrastructure as code",
        "deploy automation",
    ],
    "performance": [
        "performance testing",
        "benchmark tool",
        "profiling",
        "load testing",
    ],
    "code-review": ["code review", "pull request automation", "review tool"],
    "error-tracking": ["error tracking", "exception monitoring", "crash reporting"],
    "api": ["api testing", "api client", "rest client", "graphql tool"],
    "testing:e2e": ["end to end testing", "e2e testing", "browser testing"],
    "testing:unit": ["unit testing framework", "unit test runner"],
    "security:sast": [
        "static analysis security",
        "sast tool",
        "code analysis security",
    ],
    "security:dast": ["dynamic analysis security", "dast tool", "web security scanner"],
    "security:sca": [
        "software composition analysis",
        "dependency scanner",
        "sbom tool",
    ],
    "docs:api": ["api documentation generator", "openapi docs", "swagger tool"],
    "docs:technical": [
        "technical writing tool",
        "docs site generator",
        "knowledge base tool",
    ],
    "docs:diagrams": ["diagram as code", "mermaid tool", "architecture diagram tool"],
    "monitoring:apm": [
        "apm tool",
        "application performance monitoring",
        "distributed tracing",
    ],
    "monitoring:logs": ["log aggregator", "log analyzer", "centralized logging"],
    "monitoring:metrics": [
        "metrics collection",
        "prometheus exporter",
        "grafana dashboard",
    ],
    "ci:platform": ["ci platform", "build server", "pipeline orchestration"],
    "cd:platform": ["cd platform", "continuous deployment", "release orchestration"],
    "infra:iac": ["infrastructure as code", "terraform provider", "pulumi"],
    "infra:config": ["configuration management", "ansible role", "nix module"],
    "database:sql": ["sql client", "database gui", "sql editor"],
    "database:nosql": ["nosql client", "mongodb tool", "redis insight"],
    "database:migration": [
        "database migration tool",
        "schema migration",
        "flyway alternative",
    ],
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Phase 3: Scout — szukaj narzędzi na GitHub"
    )
    p.add_argument("--gaps", required=True, help="Comma-separated gap categories")
    p.add_argument("--max-results", type=int, default=10, help="Max results to return")
    p.add_argument("--json", action="store_true", help="Output JSON to stdout")
    p.add_argument("--output", help="Write JSON to file")
    return p.parse_args()


def check_gh():
    try:
        subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=5)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def gh_search(query, limit=10):
    try:
        r = subprocess.run(
            [
                "gh",
                "search",
                "repos",
                query,
                "--json",
                "fullName,url,stargazersCount,description,language,license,updatedAt",
                "--limit",
                str(limit),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0:
            print(
                f"warn: gh search '{query}' failed: {r.stderr.strip()}", file=sys.stderr
            )
            return []
        return json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"warn: gh search '{query}' error: {e}", file=sys.stderr)
        return []


def score_pop(stars):
    if stars < 100:
        return 2.0
    if stars < 1000:
        return 4.0
    if stars < 5000:
        return 6.0
    if stars < 10000:
        return 7.0
    if stars < 25000:
        return 8.0
    if stars < 50000:
        return 9.0
    return 10.0


def score_maint(updated_at):
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        months = (datetime.now(timezone.utc).year - dt.year) * 12 + (
            datetime.now(timezone.utc).month - dt.month
        )
        if months < 1:
            return 10.0
        if months < 3:
            return 8.0
        if months < 6:
            return 6.0
        if months < 12:
            return 4.0
        return 2.0
    except:
        return 5.0


def score_qual(desc):
    if not desc:
        return 5.0
    d = desc.lower()
    s = 5.0
    kws = {
        "test": 1.5,
        "testing": 1.5,
        "documentation": 1.5,
        "docs": 1.0,
        "framework": 1.0,
        "library": 0.5,
        "tool": 0.5,
        "cli": 0.5,
        "api": 0.5,
        "async": 0.5,
        "fast": 0.5,
        "lightweight": 0.5,
        "easy": 0.5,
        "simple": 0.5,
        "production": 1.0,
        "enterprise": 0.5,
        "scalable": 0.5,
        "extensible": 0.5,
        "modular": 0.5,
        "plugin": 0.5,
        "security": 1.0,
        "reliable": 0.5,
    }
    for kw, v in kws.items():
        if kw in d:
            s += v
    return min(10.0, s)


def score_gap(desc, queries, gap):
    if not desc:
        return 3.0
    d = desc.lower()
    s = 0.0
    for q in queries:
        words = q.lower().split()
        m = sum(1 for w in words if w in d)
        if m == len(words):
            s += 2.0
        elif m > 0:
            s += 1.0
    if gap.lower() in d:
        s += 1.0
    return min(10.0, s)


def ext_lic(lic):
    if not lic or not isinstance(lic, dict):
        return ""
    name = lic.get("name", "")
    if not name and lic.get("key"):
        name = lic["key"].upper()
    return name.replace(" License", "") if name else ""


def main():
    args = parse_args()
    gaps = [g.strip() for g in args.gaps.split(",") if g.strip()]

    empty = {
        "results": [],
        "summary": {
            "total_results": 0,
            "gaps_covered": [],
            "gaps_missing": gaps,
            "search_queries_used": [],
        },
    }

    if not gaps:
        emit(empty, args)
        return

    if not check_gh():
        empty["summary"]["note"] = (
            "gh CLI not available — install GitHub CLI (gh) for full scout functionality"
        )
        print(empty["summary"]["note"], file=sys.stderr)
        emit(empty, args)
        return

    seen = {}
    queries_used = []
    gap_covered = defaultdict(list)

    for gap in gaps:
        queries = GAP_QUERIES.get(gap, [gap.replace("-", " ")])
        for q in queries:
            queries_used.append(q)
            for repo in gh_search(q, max(5, min(20, args.max_results * 2))):
                fn = repo.get("fullName", "")
                if not fn:
                    continue

                if fn in seen:
                    if gap not in seen[fn]["gap_coverage"]:
                        seen[fn]["gap_coverage"].append(gap)
                    continue

                desc = repo.get("description") or ""
                lang = repo.get("language") or ""
                lic = ext_lic(repo.get("license"))
                stars = repo.get("stargazersCount", 0)
                updated = repo.get("updatedAt", "")

                pop = score_pop(stars)
                maint = score_maint(updated)
                qual = score_qual(desc)
                gap_rel = score_gap(desc, queries, gap)
                final = gap_rel * 0.35 + pop * 0.25 + maint * 0.20 + qual * 0.20

                seen[fn] = {
                    "repo": fn,
                    "url": repo.get("url", f"https://github.com/{fn}"),
                    "stars": stars,
                    "description": desc,
                    "language": lang,
                    "license": lic,
                    "last_updated": updated[:10] if updated else "",
                    "gap_coverage": [gap],
                    "final_score": round(final, 1),
                    "scores": {
                        "gap_relevance": round(gap_rel, 1),
                        "popularity": round(pop, 1),
                        "maintenance": round(maint, 1),
                        "quality": round(qual, 1),
                    },
                }
                gap_covered[gap].append(fn)

    results = sorted(seen.values(), key=lambda r: r["final_score"], reverse=True)[
        : args.max_results
    ]
    covered = [g for g in gaps if g in gap_covered]
    missing = [g for g in gaps if g not in gap_covered]

    out = {
        "results": results,
        "summary": {
            "total_results": len(results),
            "gaps_covered": covered,
            "gaps_missing": missing,
            "search_queries_used": queries_used,
        },
    }
    emit(out, args)


def emit(data, args):
    dumped = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(dumped, encoding="utf-8")
    if args.json:
        print(dumped)


if __name__ == "__main__":
    main()
