#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuietWire Ledger — Body Hash Computer (Pro Edition)
---------------------------------------------------
Compute a cryptographic hash of the Markdown *body* (the content after YAML
frontmatter) for canonical attestation. Optionally verify/update the
`hashes.body_sha256` field in frontmatter.

Highlights
- Robust frontmatter split; tolerant if none exists (hashes whole file).
- Deterministic normalization pipeline (optional): EOL canonicalization,
  trailing-space stripping, and HTML comment removal.
- Supports SHA-256 (default) and SHA-512.
- JSON or text table report; sidecar outputs.
- GitHub Actions annotations for mismatches.
- Optional frontmatter update (requires PyYAML) with automatic backup.

Usage
  # Hash body for entries and print report
  python tools/compute_body_hash.py --root . --glob "canonized/**/*.md" --glob "intake/**/*.md"

  # Verify against existing frontmatter and fail if mismatched
  python tools/compute_body_hash.py --root . --strict

  # Update frontmatter with computed hash (needs PyYAML)
  python tools/compute_body_hash.py --root . --update-frontmatter --strict

Exit codes
  0: success (no mismatches or non-strict mode)
  1: mismatches detected (in --strict), or update requested but missing PyYAML
  2: write/update error
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
DEFAULT_GLOBS = ["canonized/**/*.md", "intake/**/*.md", "README.md"]
DEFAULT_IGNORES = ["**/README.md"]

# ---------------- YAML helpers ----------------

def _load_yaml_safe(text: str) -> Dict:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        # minimal parser: key: value, nested maps; not a full YAML implementation
        data: Dict = {}
        stack: List[Tuple[Dict, int]] = [(data, 0)]
        cur: Optional[str] = None
        for line in text.splitlines():
            if not line.strip():
                continue
            pad = len(line) - len(line.lstrip(" "))
            while stack and pad < stack[-1][1]:
                stack.pop()
            container = stack[-1][0] if stack else data
            if line.lstrip().startswith("- "):
                val = line.strip()[2:].strip().strip('"').strip("'")
                if cur is None:
                    container.setdefault("_list_", []).append(val)
                else:
                    container.setdefault(cur, []).append(val)
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip(); v = v.strip()
                cur = None
                if v == "":
                    sub: Dict = {}
                    container[k] = sub
                    stack.append((sub, pad + 2))
                else:
                    val = v.strip().strip('"').strip("'")
                    vl = val.lower()
                    if vl in ("true","false"):
                        val = (vl == "true")
                    elif vl in ("null","none"):
                        val = None
                    container[k] = val
                    cur = k if val == "[]" else None
        return data

def parse_frontmatter(md_text: str) -> Tuple[Dict, int]:
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, 0
    return _load_yaml_safe(m.group(1)), m.end()

def update_frontmatter(md_text: str, new_fm: Dict) -> Optional[str]:
    try:
        import yaml  # type: ignore
        m = FRONTMATTER_RE.match(md_text)
        body = md_text[m.end():] if m else md_text
        dumped = yaml.safe_dump(new_fm, sort_keys=False, allow_unicode=True).rstrip()
        return f"---\n{dumped}\n---\n{body}"
    except Exception:
        return None

# ---------------- Models ----------------

@dataclass
class Record:
    path: str
    algo: str
    bytes: int
    body_hash: str
    frontmatter_hash: Optional[str]
    normalized: bool
    status: str   # ok|mismatch|updated|no_frontmatter|error
    reason: str = ""

def gha(level: str, path: Path, msg: str) -> None:
    print(f"::{level} file={path}::{msg}")

# ---------------- Core ----------------

def normalize_body(body: str, canon_eol: bool, strip_trailing_ws: bool, strip_html_comments: bool) -> str:
    s = body
    if canon_eol:
        s = s.replace("\r\n", "\n").replace("\r", "\n")
    if strip_trailing_ws:
        s = "\n".join(ln.rstrip() for ln in s.splitlines())
    if strip_html_comments:
        s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)
    return s

def digest_text(s: str, algo: str) -> str:
    if algo.lower() == "sha512":
        h = hashlib.sha512()
    else:
        h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()

def compute_for_file(p: Path, algo: str, canon_eol: bool, strip_ws: bool, strip_comments: bool, update: bool, strict: bool) -> Record:
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return Record(path=p.as_posix(), algo=algo, bytes=0, body_hash="", frontmatter_hash=None, normalized=False, status="error", reason=type(e).__name__)

    fm, fm_end = parse_frontmatter(txt)
    body = txt[fm_end:] if fm_end > 0 else txt
    normalized = False
    if canon_eol or strip_ws or strip_comments:
        body = normalize_body(body, canon_eol, strip_ws, strip_comments)
        normalized = True

    digest = digest_text(body, algo)
    declared = None
    if fm:
        declared = (fm.get("hashes") or {}).get("body_sha256")
        if declared and algo.lower() != "sha256":
            # we only verify body_sha256 against sha256 algorithm
            pass

    status = "ok"
    reason = ""
    if declared:
        if (algo.lower() == "sha256") and (declared.lower() != digest.lower()):
            status = "mismatch"
            reason = "frontmatter_hash_mismatch"

    # update frontmatter if requested
    if update:
        if not fm:
            status = "error"
            reason = "no_frontmatter_to_update"
        else:
            # ensure hashes map
            hashes = fm.setdefault("hashes", {})
            key = "body_sha256" if algo.lower() == "sha256" else f"body_{algo.lower()}"
            if hashes.get(key) != digest:
                hashes[key] = digest
                patched = update_frontmatter(txt, fm)
                if patched is None:
                    status = "error"
                    reason = "pyyaml_missing_or_dump_failed"
                else:
                    # backup original
                    p.with_suffix(p.suffix + ".bak").write_text(txt, encoding="utf-8")
                    p.write_text(patched, encoding="utf-8")
                    status = "updated"
                    reason = "frontmatter_hash_written"

    return Record(
        path=p.as_posix(),
        algo=algo.lower(),
        bytes=len(body.encode("utf-8")),
        body_hash=digest,
        frontmatter_hash=declared,
        normalized=normalized,
        status=status,
        reason=reason,
    )

# ---------------- Rendering ----------------

def render_text(rows: List[Record]) -> str:
    lines = []
    mism = upd = err = 0
    for r in rows:
        if r.status == "mismatch": mism += 1
        elif r.status == "updated": upd += 1
        elif r.status == "error": err += 1
        decl = r.frontmatter_hash[:12] + "…" if r.frontmatter_hash else "-"
        lines.append(f"[{r.status.upper()}] {r.path}  algo={r.algo} bytes={r.bytes}  hash={r.body_hash[:12]}…  declared={decl}  {r.reason}")
    lines.append(f"\nSummary: updated={upd} mismatches={mism} errors={err} total={len(rows)}")
    return "\n".join(lines)

def render_json(rows: List[Record]) -> str:
    return json.dumps([dataclasses.asdict(r) for r in rows], ensure_ascii=False, indent=2)

# ---------------- Main ----------------

def main() -> int:
    ap = argparse.ArgumentParser(description="QuietWire — Compute body hash for Markdown entries")
    ap.add_argument("--root", default=".", help="Repo root")
    ap.add_argument("--glob", action="append", default=DEFAULT_GLOBS, help="Globs to scan")
    ap.add_argument("--ignore", action="append", default=["**/.git/**"], help="Ignore patterns (fnmatch)")
    ap.add_argument("--algo", choices=["sha256","sha512"], default="sha256")
    ap.add_argument("--canon-eol", action="store_true", help="Normalize EOL to LF")
    ap.add_argument("--strip-trailing-space", action="store_true", help="Strip trailing spaces")
    ap.add_argument("--strip-html-comments", action="store_true", help="Remove <!-- ... --> blocks before hashing")
    ap.add_argument("--format", choices=["text","json"], default="text")
    ap.add_argument("--report", default="-", help="Output path or '-' for stdout")
    ap.add_argument("--sidecar", action="store_true", help="Write <file>.bodyhash.json")
    ap.add_argument("--update-frontmatter", action="store_true", help="Write computed hash into frontmatter (requires PyYAML)")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on mismatches/errors")
    args = ap.parse_args()

    root = Path(args.root)

    # Discover files
    files: List[Path] = []
    for g in args.glob:
        files.extend([p for p in root.glob(g) if p.is_file()])
    # filter ignores
    from fnmatch import fnmatch
    files = [p for p in files if not any(fnmatch(p.as_posix(), ig) for ig in args.ignore)]

    rows: List[Record] = []
    for p in files:
        rec = compute_for_file(
            p,
            algo=args.algo,
            canon_eol=args.canon_eol,
            strip_ws=args.strip_trailing_space,
            strip_comments=args.strip_html_comments,
            update=args.update_frontmatter,
            strict=args.strict,
        )
        rows.append(rec)
        if rec.status == "mismatch":
            gha("error", p, "body_hash_mismatch")
        elif rec.status == "error":
            gha("error", p, rec.reason)
        elif rec.status == "updated":
            gha("notice", p, "frontmatter_body_hash_updated")

        # sidecar
        if args.sidecar:
            try:
                sc = Path(str(p) + ".bodyhash.json")
                sc.write_text(render_json([rec]), encoding="utf-8")
            except Exception as e:
                gha("warning", p, f"sidecar_write_failed:{type(e).__name__}")

    out = render_json(rows) if args.format == "json" else render_text(rows)
    if args.report == "-" or not args.report:
        print(out)
    else:
        Path(args.report).write_text(out, encoding="utf-8")
        print(f"Report written to {args.report}")

    # Exit code
    if args.strict and any(r.status in ("mismatch","error") for r in rows):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())