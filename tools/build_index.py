#!/usr/bin/env python3
"""
QuietWire Ledger — Canonical Index Builder (Pro Edition)

Purpose
-------
Build an auditable, deterministic `INDEX.md` (or JSON) from Markdown entries
in `canonized/` and optionally `intake/`, using YAML frontmatter fields.

Highlights
----------
- Robust frontmatter parsing (uses PyYAML if available; otherwise a safe fallback).
- Sort by ISO timestamps, fallback to filename heuristics.
- Group by `ledger_stream` (configurable) and render a tidy Markdown table.
- Computes SHA-256 for each entry file for integrity hint.
- Validates minimal schema and flags errors as GitHub Actions annotations.
- Enforces unique `ledger_id` (configurable) and can fail CI on violations.
- Supports JSON output for downstream tooling.
- Zero external deps required (PyYAML is optional).

Usage
-----
    # From repo root
    python tools/build_index.py --root . --out INDEX.md

    # JSON output (to stdout unless --out provided)
    python tools/build_index.py --format json

    # Only canonized entries, strict unique IDs
    python tools/build_index.py --only-canonized --strict

Exit codes
----------
0: success
1: non-fatal issues (warnings), index written
2: fatal issues (strict mode or unique ID violations), index written (unless --no-write-on-error)
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

REQUIRED_KEYS = ["title", "ledger_id", "created_at", "canonical_status", "ledger_stream", "semantic_domain"]
REQUIRED_BLOCKS = ["classification", "retention"]

@dataclasses.dataclass
class Entry:
    path: Path
    title: str = ""
    ledger_id: str = ""
    created_at: str = ""
    canonical_status: str = ""
    ledger_stream: str = "Uncategorized"
    semantic_domain: str = ""
    sha256: str = ""
    problems: List[str] = dataclasses.field(default_factory=list)
    raw_frontmatter: Dict = dataclasses.field(default_factory=dict)
    sort_key: datetime = datetime.min

def _load_yaml_safe(text: str) -> Dict:
    """Try PyYAML; if missing, fall back to naive parser that handles simple mappings/lists."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        # Naive fallback: supports key: value and simple lists (- item)
        data: Dict = {}
        stack: List[Tuple[Dict, int]] = [(data, 0)]
        cur_list_key: Optional[str] = None
        for line in text.splitlines():
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            while stack and indent < stack[-1][1]:
                stack.pop()
            container = stack[-1][0] if stack else data
            if line.lstrip().startswith("- "):
                item = line.strip()[2:].strip().strip('"').strip("'")
                if cur_list_key is None:
                    # Attach to implicit list
                    container.setdefault("_list_", []).append(item)
                else:
                    container.setdefault(cur_list_key, []).append(item)
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                cur_list_key = None
                if v == "":
                    # start nested mapping
                    newd: Dict = {}
                    container[k] = newd
                    stack.append((newd, indent + 2))
                    cur_list_key = None
                else:
                    v = v.strip().strip('"').strip("'")
                    vl = v.lower()
                    if vl in ("true", "false"):
                        container[k] = (vl == "true")
                    elif vl in ("null", "none"):
                        container[k] = None
                    else:
                        container[k] = v
                    cur_list_key = k if v == "[]" else None
        return data

def parse_frontmatter(md_text: str) -> Tuple[Dict, int]:
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, 0
    return _load_yaml_safe(m.group(1)), m.end()

def sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(131072), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_iso(ts: str) -> Optional[datetime]:
    if not ts:
        return None
    try:
        # Accept Z suffix or offset
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return None

def derive_created_from_filename(p: Path) -> Optional[datetime]:
    # Expect YYYY-MM-DD_<slug>.md
    m = re.match(r"(\d{4}-\d{2}-\d{2})_", p.name)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1) + "T00:00:00+00:00")
    except Exception:
        return None

def collect_entries(root: Path, include_intake: bool = True, only_canonized: bool = False) -> List[Entry]:
    globs = ["canonized/**/*.md"]
    if include_intake and not only_canonized:
        globs.append("intake/**/*.md")
    entries: List[Entry] = []
    for g in globs:
        for p in root.glob(g):
            if p.is_dir() or p.name.lower() == "readme.md":
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
            fm, fm_end = parse_frontmatter(txt)
            e = Entry(path=p, raw_frontmatter=fm)
            e.title = str(fm.get("title") or p.stem)
            e.ledger_id = str(fm.get("ledger_id") or "")
            e.created_at = str(fm.get("created_at") or fm.get("timestamp") or "")
            e.canonical_status = str(fm.get("canonical_status") or "")
            e.ledger_stream = str(fm.get("ledger_stream") or "Uncategorized")
            e.semantic_domain = str(fm.get("semantic_domain") or "")
            e.sha256 = sha256_path(p)

            # Validation
            if not fm:
                e.problems.append("missing_frontmatter")
            for k in REQUIRED_KEYS:
                if k not in fm:
                    e.problems.append(f"missing_key:{k}")
            for b in REQUIRED_BLOCKS:
                if b not in fm:
                    e.problems.append(f"missing_block:{b}")

            # Sort key
            dt = parse_iso(e.created_at) or derive_created_from_filename(p) or datetime.min
            e.sort_key = dt

            if only_canonized and e.canonical_status != "canonized":
                # Skip non-canonized if the flag is set
                continue

            entries.append(e)
    # Sort newest first
    entries.sort(key=lambda x: (x.sort_key, x.title.lower()), reverse=True)
    return entries

def group_entries(entries: List[Entry], by: str) -> Dict[str, List[Entry]]:
    groups: Dict[str, List[Entry]] = {}
    if by == "none":
        groups["All"] = entries
        return groups
    for e in entries:
        key = {
            "stream": e.ledger_stream or "Uncategorized",
            "domain": e.semantic_domain or "Undeclared",
            "status": e.canonical_status or "unknown",
        }.get(by, "All")
        groups.setdefault(key, []).append(e)
    return dict(sorted(groups.items(), key=lambda kv: kv[0].lower()))

def render_markdown(groups: Dict[str, List[Entry]], heading: str) -> str:
    out: List[str] = [f"# {heading}", "", "> Auto-generated by `tools/build_index.py`. Do not edit manually."]
    if not any(groups.values()):
        out += ["", "_No entries found. Commit entries under `canonized/` (and `intake/` if enabled) with YAML frontmatter to populate this index._"]
        return "\n".join(out)
    for group, items in groups.items():
        out.append(f"\n## {group}\n")
        out += [
            "| Title | Ledger ID | Status | Created | Domain | Path | SHA256 |",
            "|---|---|---|---|---|---|---|",
        ]
        for e in items:
            out.append(
                f"| {e.title} | {e.ledger_id} | {e.canonical_status} | {e.created_at} | "
                f"{e.semantic_domain} | `{e.path.as_posix()}` | `{e.sha256[:12]}…` |"
            )
    return "\n".join(out)

def render_json(entries: List[Entry]) -> str:
    payload = []
    for e in entries:
        payload.append({
            "path": e.path.as_posix(),
            "title": e.title,
            "ledger_id": e.ledger_id,
            "created_at": e.created_at,
            "canonical_status": e.canonical_status,
            "ledger_stream": e.ledger_stream,
            "semantic_domain": e.semantic_domain,
            "sha256": e.sha256,
            "problems": e.problems,
            "sort_key": e.sort_key.isoformat() if e.sort_key else None,
        })
    return json.dumps({"entries": payload}, ensure_ascii=False, indent=2)

def annotate_gha(level: str, path: Path, msg: str) -> None:
    print(f"::{level} file={path}::{msg}")

def enforce_unique_ledger_ids(entries: List[Entry], strict: bool) -> Tuple[bool, Dict[str, List[Entry]]]:
    seen: Dict[str, List[Entry]] = {}
    ok = True
    for e in entries:
        if not e.ledger_id:
            continue
        seen.setdefault(e.ledger_id, []).append(e)
    for lid, lst in seen.items():
        if len(lst) > 1:
            ok = False
            paths = ", ".join(x.path.as_posix() for x in lst)
            for x in lst:
                annotate_gha("error", x.path, f"duplicate_ledger_id: {lid} appears in {paths}")
    if not ok and strict:
        return False, seen
    return ok, seen

def main() -> int:
    ap = argparse.ArgumentParser(description="Build canonical INDEX from ledger Markdown entries.")
    ap.add_argument("--root", default=".", help="Repository root (default: .)")
    ap.add_argument("--out", default="INDEX.md", help="Output file (Markdown unless --format json)")
    ap.add_argument("--include-intake", action="store_true", default=True, help="Include intake/ entries (default: true)")
    ap.add_argument("--only-canonized", action="store_true", help="Only include entries with canonical_status=canonized")
    ap.add_argument("--group-by", choices=["stream", "domain", "status", "none"], default="stream")
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown")
    ap.add_argument("--heading", default="📚 QuietWire Ledger — Canonical Index")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on schema errors or duplicate ledger_id")
    ap.add_argument("--require-unique-ledger-id", action="store_true", default=True)
    ap.add_argument("--no-write-on-error", action="store_true", help="Do not write output file if strict errors occur")
    args = ap.parse_args()

    root = Path(args.root)
    entries = collect_entries(root, include_intake=args.include_intake, only_canonized=args.only_canonized)

    # Emit annotations for problems
    fatal = False
    for e in entries:
        for prob in e.problems:
            level = "error" if args.strict else "warning"
            annotate_gha(level, e.path, prob)
            if args.strict:
                fatal = True

    # Unique ledger_id enforcement
    if args.require-unique-ledger_id:
        ok_unique, _ = enforce_unique_ledger_ids(entries, strict=args.strict)
        fatal = fatal or (args.strict and not ok_unique)

    # Render
    if args.format == "json":
        rendered = render_json(entries)
    else:
        groups = group_entries(entries, by=args.group_by)
        rendered = render_markdown(groups, heading=args.heading)

    # Write or stdout
    if args.format == "json" and (args.out == "-" or not args.out):
        print(rendered)
    else:
        if fatal and args.no_write_on_error:
            print("Fatal issues detected; skipping write due to --no-write-on-error.", file=sys.stderr)
        else:
            out_path = Path(args.out)
            out_path.write_text(rendered, encoding="utf-8")
            print(f"INDEX written to {out_path}")

    # Exit code
    if fatal:
        return 2
    # If there were warnings (non-strict), still return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())