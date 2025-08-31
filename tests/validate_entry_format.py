#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuietWire Ledger — Entry Format Validator (Pro Edition)
------------------------------------------------------
Validate Markdown ledger entries against canonical frontmatter schema,
security rules, and minimal content constraints. Optionally verify the
body hash (`hashes.body_sha256`) using a deterministic normalization
pipeline identical to `tools/compute_body_hash.py`.

Highlights
- YAML frontmatter parsing (PyYAML if available, robust fallback otherwise).
- Schema validation (required/optional fields) with helpful messages.
- Timestamp validation (ISO-8601 WITH timezone).
- Authors/validators/witness fields as string OR list[string].
- Attachments/provenance structure checks + local path existence.
- Optional body-hash verification with normalization.
- Security lint: disallow <script> in body, forbidden URI schemes, large inline data URIs.
- GitHub Actions annotations for errors/warnings.
- Text/JSON reports; strict mode to fail CI on warnings.

Usage
  python tools/validate_entry_format.py --root . \
    --glob "canonized/**/*.md" --glob "intake/**/*.md" \
    --verify-body-hash --canon-eol --strip-trailing-space --strip-html-comments \
    --format text --report validate.txt --strict

Exit codes
  0: OK
  1: Errors (or warnings in --strict)
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^\s{0,3}(?P<level>#{1,6})\s+(?P<text>.+?)\s*#*\s*$")
FORBIDDEN_SCHEMES = {"javascript", "file", "vbscript", "data"}
SKIP_SCHEMES = {"mailto", "tel"}

DEFAULT_GLOBS = ["canonized/**/*.md", "intake/**/*.md"]
DEFAULT_IGNORES = ["**/.git/**", "**/README.md", "**/attachments/**"]

# ---------------- YAML helpers ----------------

def _load_yaml_safe(text: str) -> Dict:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        # extremely small fallback: "key: value", nested maps, simple lists "- item"
        data: Dict = {}
        stack: List[Tuple[Dict, int]] = [(data, 0)]
        cur_key: Optional[str] = None
        for raw in text.splitlines():
            if not raw.strip(): 
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            while stack and indent < stack[-1][1]:
                stack.pop()
            container = stack[-1][0] if stack else data
            line = raw.strip()
            if line.startswith("- "):
                item = line[2:].strip().strip('"').strip("'")
                if cur_key is None:
                    container.setdefault("_list_", []).append(item)
                else:
                    container.setdefault(cur_key, []).append(item)
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip(); v = v.strip()
                cur_key = None
                if v == "":
                    sub: Dict = {}
                    container[k] = sub
                    stack.append((sub, indent + 2))
                else:
                    val = v.strip().strip('"').strip("'")
                    low = val.lower()
                    if low in ("true","false"):
                        val = (low == "true")
                    elif low in ("null","none"):
                        val = None
                    container[k] = val
                    cur_key = k if val == "[]" else None
        return data

def parse_frontmatter(md_text: str) -> Tuple[Dict, int]:
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, 0
    return _load_yaml_safe(m.group(1)), m.end()

# ---------------- Normalization & hashing ----------------

def normalize_body(body: str, canon_eol: bool, strip_trailing_ws: bool, strip_html_comments: bool) -> str:
    s = body
    if canon_eol:
        s = s.replace("\r\n", "\n").replace("\r", "\n")
    if strip_trailing_ws:
        s = "\n".join(ln.rstrip() for ln in s.splitlines())
    if strip_html_comments:
        s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)
    return s

def sha256_text(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()

# ---------------- Models ----------------

@dataclass
class Finding:
    level: str           # error|warning|notice
    path: str
    code: str
    message: str
    line: Optional[int] = None

def gha(level: str, path: Path, line: Optional[int], msg: str) -> None:
    if line is not None:
        print(f"::{level} file={path},line={line}::{msg}")
    else:
        print(f"::{level} file={path}::{msg}")

# ---------------- Validation helpers ----------------

ISO_TZ = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+\-]\d{2}:\d{2})$")

def _as_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    return [str(x).strip()]

def has_h1(body: str) -> bool:
    for ln in body.splitlines():
        if HEADING_RE.match(ln):
            level = HEADING_RE.match(ln).group("level")
            if len(level) == 1:
                return True
    return False

def scan_forbidden_schemes(body: str) -> List[Tuple[int, str]]:
    out: List[Tuple[int,str]] = []
    url_re = re.compile(r"\((?P<url>[a-zA-Z][a-zA-Z0-9+\.-]*:[^)]+)\)")  # (scheme:...)
    for i, line in enumerate(body.splitlines(), start=1):
        for m in url_re.finditer(line):
            scheme = m.group("url").split(":")[0].lower()
            if scheme in FORBIDDEN_SCHEMES:
                out.append((i, scheme))
    return out

def scan_script_tags(body: str) -> List[int]:
    lines: List[int] = []
    for i, ln in enumerate(body.splitlines(), start=1):
        if "<script" in ln.lower():
            lines.append(i)
    return lines

def validate_timestamp(ts: str) -> bool:
    if not isinstance(ts, str): 
        return False
    return bool(ISO_TZ.match(ts))

def validate_sha256_hex(s: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", s or ""))

# ---------------- Core validation for a single file ----------------

REQUIRED_FIELDS = [
    "title", "author", "timestamp", "ledger_stream", "semantic_domain", "attestation"
]

def validate_entry(path: Path, text: str, verify_hash: bool, canon_eol: bool, strip_ws: bool, strip_comments: bool) -> List[Finding]:
    findings: List[Finding] = []
    fm, fm_end = parse_frontmatter(text)
    if not fm:
        findings.append(Finding("error", str(path), "missing_frontmatter", "Entry lacks YAML frontmatter at the top (--- ... ---)."))
        return findings

    # Required presence
    for k in REQUIRED_FIELDS:
        if k not in fm or fm.get(k) in (None, "", []):
            findings.append(Finding("error", str(path), "missing_field", f"Missing required field `{k}` in frontmatter."))

    # Types / formats
    if "timestamp" in fm and fm.get("timestamp") and not validate_timestamp(fm.get("timestamp")):
        findings.append(Finding("error", str(path), "bad_timestamp", "timestamp must be ISO-8601 with timezone, e.g., 2025-08-31T12:30+03:00 or ...Z"))

    # Authors & signers
    for field in ("author", "validated_by", "witness"):
        if field in fm and fm.get(field) not in (None, ""):
            vals = _as_list(fm.get(field))
            if not vals:
                findings.append(Finding("warning", str(path), "empty_list", f"`{field}` is empty."))

    # Attestation must be boolean
    if "attestation" in fm and not isinstance(fm.get("attestation"), bool):
        findings.append(Finding("error", str(path), "bad_attestation_type", "`attestation` must be boolean (true/false)."))

    # Hashes: body + attachments
    hashes = fm.get("hashes") or {}
    if "body_sha256" not in hashes or not hashes.get("body_sha256"):
        findings.append(Finding("warning", str(path), "missing_body_hash", "hashes.body_sha256 is missing."))
    else:
        if not validate_sha256_hex(hashes.get("body_sha256")):
            findings.append(Finding("error", str(path), "bad_body_hash_format", "hashes.body_sha256 must be 64-hex."))

    # Verify body hash if requested
    body = text[fm_end:] if fm_end > 0 else ""
    if verify_hash and body:
        normalized = normalize_body(body, canon_eol, strip_ws, strip_comments)
        digest = sha256_text(normalized)
        declared = (hashes or {}).get("body_sha256")
        if declared and declared.lower() != digest.lower():
            findings.append(Finding("error", str(path), "body_hash_mismatch", "Body hash does not match frontmatter hashes.body_sha256."))

    # Attachments schema
    atts = (hashes.get("attachments") or [])
    if isinstance(atts, dict):
        # allow mapping {path: sha256}, but recommend list form
        findings.append(Finding("warning", str(path), "attachments_mapping_form", "hashes.attachments should be a list of dicts with path/sha256/size; mapping form is discouraged."))
        for pth, sha in atts.items():
            if not pth:
                findings.append(Finding("error", str(path), "attachment_no_path", "attachments mapping has empty key."))
                continue
            if sha and not validate_sha256_hex(str(sha)):
                findings.append(Finding("warning", str(path), "attachment_sha_format", f"Attachment `{pth}` has non-hex sha256."))
            p = (path.parent / pth).resolve()
            if not p.exists():
                findings.append(Finding("error", str(path), "attachment_missing", f"Attachment path not found: {pth}"))
    elif isinstance(atts, list):
        for i, it in enumerate(atts):
            if isinstance(it, str):
                pth = it
                p = (path.parent / pth).resolve()
                if not p.exists():
                    findings.append(Finding("error", str(path), "attachment_missing", f"[attachments[{i}]] not found: {pth}"))
            elif isinstance(it, dict):
                pth = str(it.get("path","")).strip()
                if not pth:
                    findings.append(Finding("error", str(path), "attachment_no_path", f"[attachments[{i}]] missing `path`."))
                else:
                    p = (path.parent / pth).resolve()
                    if not p.exists():
                        findings.append(Finding("error", str(path), "attachment_missing", f"[attachments[{i}]] not found: {pth}"))
                sha = it.get("sha256")
                if sha and not validate_sha256_hex(str(sha)):
                    findings.append(Finding("warning", str(path), "attachment_sha_format", f"[attachments[{i}]] sha256 must be 64-hex."))
                size = it.get("size")
                if size is not None:
                    try:
                        if int(size) <= 0:
                            findings.append(Finding("warning", str(path), "attachment_size", f"[attachments[{i}]] size should be > 0."))
                    except Exception:
                        findings.append(Finding("warning", str(path), "attachment_size", f"[attachments[{i}]] size is not an integer."))

    # Provenance chain
    prov = (fm.get("provenance") or {})
    chain = prov.get("evidence_chain") or []
    if chain and not isinstance(chain, list):
        findings.append(Finding("error", str(path), "bad_provenance_type", "provenance.evidence_chain must be a list."))
    for j, node in enumerate(chain if isinstance(chain, list) else []):
        if isinstance(node, dict):
            pth = (node.get("path") or "").strip()
            href = (node.get("href") or "").strip()
            if not pth and not href:
                findings.append(Finding("warning", str(path), "prov_empty_node", f"[evidence_chain[{j}]] should have `path` or `href`."))
            if pth:
                p = (path.parent / pth).resolve()
                if not p.exists():
                    findings.append(Finding("warning", str(path), "prov_path_missing", f"[evidence_chain[{j}]] local path not found: {pth}"))
            if href:
                # basic scheme check
