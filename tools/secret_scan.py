#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuietWire Ledger — Secret Scanner (Pro Edition)
-----------------------------------------------
Scan Markdown/YAML/JSON/TEXT for leaked credentials, tokens and private keys.

Highlights
- Curated regex signatures (AWS, GitHub, Slack, Google, Stripe, Twilio, RSA/SSH, etc.).
- Shannon entropy heuristic for generic high-entropy strings.
- Allowlist via `.secretignore` (regex per line) for tokens or file paths.
- Baseline support (`.secret-baseline.json`) to suppress known historical findings (until rotated).
- GitHub Actions annotations for inline feedback.
- JSON or text reports; configurable fail level (strict mode). 100% stdlib.

Usage
  python tools/secret_scan.py --root . --format text --strict
  python tools/secret_scan.py --root . --update-baseline    # refresh baseline with current findings

Exit codes
  0: no findings (or only ignored/baselined)
  1: findings present (or warnings in --strict)
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from hashlib import sha256
from math import log2
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_GLOBS = [
    "**/*.md","**/*.markdown",
    "**/*.yml","**/*.yaml",
    "**/*.json","**/*.env",
    "**/*.txt",".github/**/*.yml",
]
DEFAULT_IGNORES = ["**/.git/**","**/attachments/**","**/node_modules/**"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# ---------------- RegEx Signatures (compiled) ----------------

SIGS: Dict[str, re.Pattern] = {
    # Cloud / API
    "AWS_ACCESS_KEY_ID": re.compile(r"\b(A3T|AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b"),
    "AWS_SECRET_ACCESS_KEY": re.compile(r"(?i)\baws(.{0,20})?(secret|sk|access.?key)\b.{0,3}([0-9A-Za-z/+]{40})"),
    "GITHUB_TOKEN": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{82,})\b"),
    "SLACK_TOKEN": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,48}\b"),
    "SLACK_WEBHOOK": re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]{20,}"),
    "GOOGLE_API_KEY": re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    "GOOGLE_OAUTH": re.compile(r"\bya29\.[0-9A-Za-z\-_]+\b"),
    "STRIPE_KEY": re.compile(r"\b(sk|rk|pk)_(live|test)_[0-9A-Za-z]{16,}\b"),
    "TWILIO_AUTH": re.compile(r"\b[0-9a-fA-F]{32}\b(?=.*\bTwilio\b)"),
    "SENDGRID_KEY": re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b"),
    "AZURE_CONN": re.compile(r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+;"),
    # Keys / Certs
    "RSA_PRIVATE_KEY": re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA|PRIVATE) PRIVATE KEY-----"),
    "SSH_PRIVATE_KEY": re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"),
    # Generic
    "GENERIC_BEARER": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-\._~\+/]+=*\b"),
    "JWT_TOKEN": re.compile(r"\beyJ[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\b"),
}

# ------------- Data models -------------

@dataclass
class Finding:
    kind: str
    path: str
    line: int
    span: Tuple[int,int]
    preview: str
    severity: str  # high|medium|low
    reason: str = ""
    entropy: Optional[float] = None
    suppressed: bool = False

def gha(level: str, path: Path, line: int, msg: str) -> None:
    print(f"::{level} file={path},line={line}::{msg}")

# ------------- Helpers -------------

def is_binary_blob(data: bytes) -> bool:
    return b"\x00" in data[:4096]

def shannon_entropy(s: str) -> float:
    if not s: return 0.0
    alphabet = {}
    for ch in s:
        alphabet[ch] = alphabet.get(ch, 0) + 1
    n = len(s)
    return -sum((c/n) * log2(c/n) for c in alphabet.values())

def preview_token(tok: str, head: int = 6, tail: int = 4) -> str:
    if len(tok) <= head + tail:
        return tok
    return tok[:head] + "…" + tok[-tail:]

def load_allowlist(path: Path) -> List[re.Pattern]:
    if not path.exists(): return []
    pats = []
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        try:
            pats.append(re.compile(ln))
        except Exception:
            # ignore bad regex lines
            pass
    return pats

def in_allowlist(token: str, file_path: str, allowlist: List[re.Pattern]) -> bool:
    for rx in allowlist:
        if rx.search(token) or rx.search(file_path):
            return True
    return False

def load_baseline(path: Path) -> Dict[str, List[str]]:
    if not path.exists(): return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_baseline(path: Path, findings: List[Finding]) -> None:
    payload: Dict[str, List[str]] = {}
    for f in findings:
        payload.setdefault(f.path, []).append(f.kind + ":" + f.preview)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def is_baselined(f: Finding, baseline: Dict[str, List[str]]) -> bool:
    arr = baseline.get(f.path, [])
    key = f.kind + ":" + f.preview
    return key in arr

# ------------- Scanning -------------

def scan_text(text: str, file_path: str, allowlist: List[re.Pattern], entropy_threshold: float) -> List[Finding]:
    findings: List[Finding] = []
    lines = text.splitlines()
    # Signature hits
    for i, line in enumerate(lines, start=1):
        for kind, rx in SIGS.items():
            for m in rx.finditer(line):
                token = m.group(0)
                if in_allowlist(token, file_path, allowlist):
                    continue
                sev = "high" if "PRIVATE_KEY" in kind or "AWS_SECRET" in kind else "medium"
                findings.append(Finding(
                    kind=kind, path=file_path, line=i, span=(m.start(), m.end()),
                    preview=preview_token(token), severity=sev, reason="signature",
                ))
        # High-entropy heuristic (skip very short)
        for m in re.finditer(r"[A-Za-z0-9_\-\.\/\+]{20,}", line):
            token = m.group(0)
            if in_allowlist(token, file_path, allowlist):
                continue
            # skip obviously benign patterns
            if token.endswith((".md",".html",".png",".jpg",".jpeg",".gif",".svg")): 
                continue
            H = shannon_entropy(token)
            if H >= entropy_threshold:
                findings.append(Finding(
                    kind="HIGH_ENTROPY", path=file_path, line=i, span=(m.start(), m.end()),
                    preview=preview_token(token), severity="low", reason="entropy", entropy=H
                ))
    return findings

def scan_file(p: Path, allowlist: List[re.Pattern], entropy_threshold: float) -> List[Finding]:
    try:
        data = p.read_bytes()
    except Exception:
        return []
    if len(data) > MAX_FILE_SIZE or is_binary_blob(data):
        return []  # skip large or binary
    try:
        txt = data.decode("utf-8", errors="ignore")
    except Exception:
        return []
    return scan_text(txt, p.as_posix(), allowlist, entropy_threshold)

# ------------- Output -------------

def render_text(findings: List[Finding]) -> str:
    lines: List[str] = []
    counts = {"high":0,"medium":0,"low":0}
    for f in findings:
        counts[f.severity] += 1
        ent = f" entropy={f.entropy:.2f}" if f.entropy is not None else ""
        sup = " (suppressed)" if f.suppressed else ""
        lines.append(f"[{f.severity.upper()}] {f.path}:{f.line} {f.kind} => {f.preview}{ent}{sup}")
    lines.append(f"\nSummary: high={counts['high']} medium={counts['medium']} low={counts['low']} total={len(findings)}")
    return "\n".join(lines)

def render_json(findings: List[Finding]) -> str:
    return json.dumps([dataclasses.asdict(f) for f in findings], ensure_ascii=False, indent=2)

# ------------- Main -------------

def main() -> int:
    ap = argparse.ArgumentParser(description="QuietWire — Secret Scanner")
    ap.add_argument("--root", default=".", help="Repo root")
    ap.add_argument("--glob", action="append", default=DEFAULT_GLOBS, help="Glob(s) to scan")
    ap.add_argument("--ignore", action="append", default=DEFAULT_IGNORES, help="Ignore patterns (fnmatch)")
    ap.add_argument("--allowlist", default=".secretignore", help="Regex allowlist file")
    ap.add_argument("--baseline", default=".secret-baseline.json", help="Baseline json path")
    ap.add_argument("--update-baseline", action="store_true", help="Write current findings to baseline and exit 0")
    ap.add_argument("--entropy-threshold", type=float, default=3.6, help="Shannon entropy threshold for generic tokens")
    ap.add_argument("--format", choices=["text","json"], default="text")
    ap.add_argument("--report", default="-", help="Output path or '-' for stdout")
    ap.add_argument("--strict", action="store_true", help="Treat low/medium as failure")
    args = ap.parse_args()

    root = Path(args.root)
    allow = load_allowlist(root / args.allowlist)
    baseline = load_baseline(root / args.baseline)

    # Gather files
    files: List[Path] = []
    for g in args.glob:
        files.extend([p for p in root.glob(g) if p.is_file()])
    files = [p for p in files if not any(fnmatch(p.as_posix(), ig) for ig in args.ignore)]

    # Scan
    findings: List[Finding] = []
    for p in files:
        findings.extend(scan_file(p, allow, args.entropy_threshold))

    # Baseline suppression
    for f in findings:
        if is_baselined(f, baseline):
            f.suppressed = True

    if args.update_baseline:
        save_baseline(root / args.baseline, [f for f in findings if not f.suppressed])
        print(f"Baseline updated: {args.baseline} ({len(findings)} findings captured)")
        return 0

    # Emit GHA annotations
    highs = meds = lows = 0
    actives: List[Finding] = []
    for f in findings:
        if f.suppressed:
            continue
        actives.append(f)
        if f.severity == "high": highs += 1
        elif f.severity == "medium": meds += 1
        else: lows += 1

        level = "error" if (f.severity in ("high","medium") or args.strict) else "warning"
        msg = f"{f.kind} => {f.preview} ({f.reason})"
        gha(level, Path(f.path), f.line, msg)

    # Render report
    out = render_json(findings) if args.format == "json" else render_text(findings)
    if args.report == "-" or not args.report:
        print(out)
    else:
        Path(args.report).write_text(out, encoding="utf-8")
        print(f"Report written to {args.report}")

    # Exit code
    if actives:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())