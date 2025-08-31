#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuietWire Ledger — Attachment Hasher & Verifier (Pro Edition)
-------------------------------------------------------------
Compute SHA-256 for attachments referenced by Markdown entries and verify
declared hashes/sizes in YAML frontmatter.

Highlights
- Parses YAML frontmatter (uses PyYAML if present, else safe fallback).
- Supports `hashes.attachments[]` (dict or string items) and
  `provenance.evidence_chain[]` (with local `path`).
- Streams hashing for large files; concurrency for speed.
- Verifies presence, size and sha256 (if declared); emits GHA annotations.
- Text or JSON report; strict mode to fail CI on mismatch/missing.
- Optional sidecar JSON write with computed results per entry.
- Optional frontmatter update (requires PyYAML) with safe backup.

Usage
  # Verify all canonized + intake entries
  python tools/hash_attachments.py --root . --glob "canonized/**/*.md" --glob "intake/**/*.md"

  # Write sidecar reports (entry.md.hashes.json)
  python tools/hash_attachments.py --root . --sidecar

  # Attempt to patch frontmatter (requires PyYAML). Backup kept as entry.md.bak
  python tools/hash_attachments.py --root . --update-frontmatter --strict

Exit codes
  0: all good
  1: mismatches/missing detected
  2: write/update error (when --update-frontmatter)
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

DEFAULT_GLOBS = ["canonized/**/*.md","intake/**/*.md"]
DEFAULT_IGNORES = ["**/README.md"]
CHUNK = 256 * 1024

# ---------------- YAML ----------------

def _load_yaml_safe(text: str) -> Dict:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        # minimal parser: key: value and nested maps, simple lists
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
                # attach to last key
                if cur_list_key is None:
                    container.setdefault("_list_", []).append(item)
                else:
                    container.setdefault(cur_list_key, []).append(item)
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip(); v = v.strip()
                cur_list_key = None
                if v == "":
                    newd: Dict = {}
                    container[k] = newd
                    stack.append((newd, indent + 2))
                else:
                    val = v.strip().strip('"').strip("'")
                    vl = val.lower()
                    if vl in ("true","false"):
                        val = (vl == "true")
                    elif vl in ("null","none"):
                        val = None
                    container[k] = val
                    cur_list_key = k if val == "[]" else None
        return data

def parse_frontmatter(md_text: str) -> Tuple[Dict, int]:
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, 0
    return _load_yaml_safe(m.group(1)), m.end()

def update_frontmatter(md_text: str, new_fm: Dict) -> Optional[str]:
    """Rewrite frontmatter with PyYAML if available, else return None."""
    try:
        import yaml  # type: ignore
        m = FRONTMATTER_RE.match(md_text)
        body = md_text[m.end():] if m else md_text
        dumped = yaml.safe_dump(new_fm, sort_keys=False, allow_unicode=True).rstrip()
        return f"---\n{dumped}\n---\n{body}"
    except Exception:
        return None

# ---------------- Data model ----------------

@dataclass
class AttachmentRef:
    entry: Path            # markdown entry path
    path: Path             # resolved local path
    fm_path: str           # as declared in frontmatter (raw)
    declared_sha256: Optional[str] = None
    declared_size: Optional[int] = None

@dataclass
class Result:
    entry: str
    attachment: str
    exists: bool
    size: Optional[int]
    sha256: Optional[str]
    status: str           # ok|missing|mismatch|external|error
    reason: str = ""

def gha(level: str, path: Path, msg: str) -> None:
    print(f"::{level} file={path}::{msg}")

# ---------------- Collection ----------------

def _collect_from_hashes(fm: Dict, entry_path: Path) -> List[AttachmentRef]:
    out: List[AttachmentRef] = []
    hashes = (fm.get("hashes") or {})
    items = hashes.get("attachments") or []
    if isinstance(items, dict):
        # tolerate mapping {path: sha256}
        for k,v in items.items():
            out.append(AttachmentRef(entry=entry_path, path=(entry_path.parent / k).resolve(), fm_path=str(k), declared_sha256=str(v)))
        return out
    if not isinstance(items, list):
        return out
    for it in items:
        if isinstance(it, str):
            if it.startswith("http://") or it.startswith("https://"):
                continue
            out.append(AttachmentRef(entry=entry_path, path=(entry_path.parent / it).resolve(), fm_path=it))
        elif isinstance(it, dict):
            p = str(it.get("path","")).strip()
            if not p:
                continue
            if p.startswith("http://") or p.startswith("https://"):
                continue
            out.append(AttachmentRef(
                entry=entry_path,
                path=(entry_path.parent / p).resolve(),
                fm_path=p,
                declared_sha256=(str(it.get("sha256")) if it.get("sha256") else None),
                declared_size=(int(it.get("size")) if str(it.get("size","")).isdigit() else None),
            ))
    return out

def _collect_from_provenance(fm: Dict, entry_path: Path) -> List[AttachmentRef]:
    out: List[AttachmentRef] = []
    prov = (fm.get("provenance") or {})
    chain = prov.get("evidence_chain") or []
    if not isinstance(chain, list):
        return out
    for it in chain:
        if isinstance(it, dict):
            p = (it.get("path") or "").strip()
            href = (it.get("href") or "").strip()
            target = p or href
            if not target or target.startswith("http://") or target.startswith("https://"):
                continue
            out.append(AttachmentRef(entry=entry_path, path=(entry_path.parent / target).resolve(), fm_path=target))
    return out

def collect_attachments(entry_path: Path, fm: Dict) -> List[AttachmentRef]:
    refs = _collect_from_hashes(fm, entry_path) + _collect_from_provenance(fm, entry_path)
    # de-duplicate by absolute path
    uniq: Dict[Path, AttachmentRef] = {}
    for r in refs:
        uniq[r.path] = r
    return list(uniq.values())

# ---------------- Hashing ----------------

def sha256_file(p: Path) -> Tuple[int, str]:
    h = hashlib.sha256()
    total = 0
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
            total += len(chunk)
    return total, h.hexdigest()

def verify_attachment(ref: AttachmentRef) -> Result:
    if not ref.path.exists() or not ref.path.is_file():
        return Result(entry=ref.entry.as_posix(), attachment=ref.fm_path, exists=False, size=None, sha256=None, status="missing", reason="file_not_found")
    try:
        size, digest = sha256_file(ref.path)
    except Exception as e:
        return Result(entry=ref.entry.as_posix(), attachment=ref.fm_path, exists=True, size=None, sha256=None, status="error", reason=type(e).__name__)
    # Compare
    if ref.declared_size is not None and size != ref.declared_size:
        return Result(entry=ref.entry.as_posix(), attachment=ref.fm_path, exists=True, size=size, sha256=digest, status="mismatch", reason="size_mismatch")
    if ref.declared_sha256 and ref.declared_sha256.lower() != digest.lower():
        return Result(entry=ref.entry.as_posix(), attachment=ref.fm_path, exists=True, size=size, sha256=digest, status="mismatch", reason="sha256_mismatch")
    return Result(entry=ref.entry.as_posix(), attachment=ref.fm_path, exists=True, size=size, sha256=digest, status="ok", reason="verified")

# ---------------- Frontmatter patching ----------------

def try_update_entry(entry_path: Path, fm: Dict, results: List[Result], backup: bool = True) -> bool:
    """Patch fm.hashes.attachments[i].sha256/size if missing; requires PyYAML. Returns True if updated."""
    try:
        import yaml  # type: ignore
    except Exception:
        return False
    updated = False
    # Build quick lookup by fm_path
    by_path: Dict[str, Result] = {r.attachment: r for r in results if r.exists and r.sha256}
    # normalize structure
    hashes = fm.setdefault("hashes", {})
    arr = hashes.get("attachments")
    if isinstance(arr, dict):
        # convert mapping to list of dicts to avoid ambiguity
        new_list = []
        for k,v in arr.items():
            r = by_path.get(str(k))
            if r:
                new_list.append({"path": k, "sha256": r.sha256, "size": r.size})
                updated = True
            else:
                new_list.append({"path": k, "sha256": v})
        hashes["attachments"] = new_list
        updated = True
    elif isinstance(arr, list):
        for it in arr:
            if isinstance(it, dict):
                p = str(it.get("path",""))
                r = by_path.get(p)
                if r:
                    if not it.get("sha256"):
                        it["sha256"] = r.sha256; updated = True
                    if not it.get("size"):
                        it["size"] = r.size; updated = True
            elif isinstance(it, str):
                r = by_path.get(it)
                if r:
                    # promote to dict with computed values
                    idx = arr.index(it)
                    arr[idx] = {"path": it, "sha256": r.sha256, "size": r.size}
                    updated = True
    else:
        # create new attachments section
        lst = []
        for r in results:
            if r.exists and r.sha256:
                lst.append({"path": r.attachment, "sha256": r.sha256, "size": r.size})
        if lst:
            hashes["attachments"] = lst
            updated = True

    if not updated:
        return False

    # Write back with backup
    md = entry_path.read_text(encoding="utf-8", errors="ignore")
    patched = update_frontmatter(md, fm)
    if not patched:
        return False
    if backup:
        entry_path.with_suffix(entry_path.suffix + ".bak").write_text(md, encoding="utf-8")
    entry_path.write_text(patched, encoding="utf-8")
    return True

# ---------------- Reporting ----------------

def render_text(results: List[Result]) -> str:
    lines = []
    ok = miss = mm = err = 0
    for r in results:
        if r.status == "ok": ok += 1
        elif r.status == "missing": miss += 1
        elif r.status == "mismatch": mm += 1
        elif r.status == "error": err += 1
        size = r.size if r.size is not None else "-"
        sha = (r.sha256[:12] + "…") if r.sha256 else "-"
        lines.append(f"[{r.status.upper()}] {r.entry} :: {r.attachment}  size={size}  sha256={sha}  {r.reason}")
    lines.append(f"\nSummary: ok={ok} missing={miss} mismatch={mm} error={err} total={len(results)}")
    return "\n".join(lines)

def render_json(results: List[Result]) -> str:
    return json.dumps([dataclasses.asdict(r) for r in results], ensure_ascii=False, indent=2)

# ---------------- Main ----------------

def main() -> int:
    ap = argparse.ArgumentParser(description="QuietWire — Attachment hasher/verifier")
    ap.add_argument("--root", default=".", help="Repo root")
    ap.add_argument("--glob", action="append", default=DEFAULT_GLOBS, help="Entry globs")
    ap.add_argument("--ignore", action="append", default=DEFAULT_IGNORES, help="Ignore patterns")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--format", choices=["text","json"], default="text")
    ap.add_argument("--report", default="-", help="Output path or '-' for stdout")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on any missing/mismatch")
    ap.add_argument("--sidecar", action="store_true", help="Write <entry>.hashes.json with computed results")
    ap.add_argument("--update-frontmatter", action="store_true", help="Patch YAML frontmatter with computed sha256/size (requires PyYAML)")
    args = ap.parse_args()

    root = Path(args.root)

    # collect entries
    entries: List[Path] = []
    for g in args.glob:
        entries.extend([p for p in root.glob(g) if p.is_file()])
    # filter ignores
    from fnmatch import fnmatch
    entries = [p for p in entries if not any(fnmatch(p.as_posix(), ig) for ig in args.ignore)]

    all_results: List[Result] = []
    write_errors = False

    for entry in entries:
        md = entry.read_text(encoding="utf-8", errors="ignore")
        fm, _ = parse_frontmatter(md)
        if not fm:
            gha("warning", entry, "missing_frontmatter")
            continue
        refs = collect_attachments(entry, fm)
        if not refs:
            continue

        # hash concurrently
        results: List[Result] = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(verify_attachment, r): r for r in refs}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                # annotate failures
                if r.status == "missing":
                    gha("error", Path(r.entry), f"attachment_missing: {r.attachment}")
                elif r.status == "mismatch":
                    gha("error", Path(r.entry), f"attachment_mismatch({r.reason}): {r.attachment}")
                elif r.status == "error":
                    gha("error", Path(r.entry), f"attachment_error: {r.attachment} ({r.reason})")

        all_results.extend(results)

        # sidecar
        if args.sidecar:
            try:
                side = Path(str(entry) + ".hashes.json")
                side.write_text(render_json(results), encoding="utf-8")
            except Exception as e:
                write_errors = True
                gha("error", entry, f"sidecar_write_failed: {type(e).__name__}")

        # update frontmatter
        if args.update_frontmatter:
            try:
                updated = try_update_entry(entry, fm, results, backup=True)
                if not updated:
                    gha("warning", entry, "frontmatter_update_skipped_or_failed")
            except Exception as e:
                write_errors = True
                gha("error", entry, f"frontmatter_update_failed: {type(e).__name__}")

    # render global report
    out = render_json(all_results) if args.format == "json" else render_text(all_results)
    if args.report == "-" or not args.report:
        print(out)
    else:
        Path(args.report).write_text(out, encoding="utf-8")
        print(f"Report written to {args.report}")

    # exit code
    had_problem = any(r.status in ("missing","mismatch","error") for r in all_results)
    if write_errors:
        return 2
    if had_problem and args.strict:
        return 1
    # Non-strict: allow OK exit even with problems (annotations emitted)
    return 0

if __name__ == "__main__":
    sys.exit(main())
``` [❶](code://python)