#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuietWire Ledger - Link Checker (Pro Edition)
Validate external (HTTP/HTTPS) and internal (relative) links in Markdown files.
"""

from __future__ import annotations

import argparse
import dataclasses
import ipaddress
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

# --------------------------- Config & Regex ---------------------------

LINK_RE = re.compile(
    r"""
    (?:!?\[[^\]]*\]\((?P<md>[^)]+)\))        # Markdown [text](URL) or image ![...](URL)
    | <(?P<angle>https?://[^>\s]+)>          # Autolink <http://...>
    | (?<!\()(?P<bare>https?://[^\s)]+)      # Bare URL not immediately after '('
    """,
    re.VERBOSE,
)

HEADING_RE = re.compile(r"^\s{0,3}(?P<level>#{1,6})\s+(?P<text>.+?)\s*#*\s*$")
PUNCT_RE = re.compile(r"[^\w\- ]+", re.UNICODE)

DEFAULT_GLOBS = ["canonized/**/*.md", "intake/**/*.md", "README.md", "INDEX.md"]
DEFAULT_IGNORES = ["**/.git/**", "**/attachments/**"]
FORBIDDEN_SCHEMES = {"javascript", "file", "data"}
SKIP_SCHEMES = {"mailto", "tel"}
PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

UA = "QuietWire-LinkChecker/1.1"

# --------------------------- Data model ---------------------------

@dataclass
class Finding:
    path: str
    line: int
    url: str
    link_type: str  # external|internal
    status: str     # ok|error|warning|skip
    reason: str = ""
    http_code: Optional[int] = None
    final_url: Optional[str] = None

# --------------------------- Utilities ---------------------------

def gha(level: str, path: Path, line: int, msg: str) -> None:
    # GitHub Actions workflow command
    print(f"::{level} file={path},line={line}::{msg}")

def normalize_url(url: str) -> str:
    url = url.strip().strip(").,;")
    try:
        u = urlparse(url)
        if u.scheme in ("http", "https"):
            path = re.sub(r"//+", "/", u.path) or "/"
            return urlunparse((u.scheme, u.netloc, path, u.params, u.query, u.fragment))
    except Exception:
        pass
    return url

def is_private_host(host: str) -> bool:
    if not host:
        return True
    try:
        ip = ipaddress.ip_address(host)
        return any(ip in n for n in PRIVATE_NETS)
    except ValueError:
        return host.lower() in {"localhost", "localhost.localdomain", "0.0.0.0"}

def http_ok(url: str, timeout: float = 8.0, max_redirects: int = 5) -> Tuple[bool, Optional[int], Optional[str], str]:
    # Returns ok, status_code, final_url, reason
    seen = 0
    method = "HEAD"
    current = url
    while seen <= max_redirects:
        req = Request(current, method=method, headers={"User-Agent": UA})
        try:
            with closing(urlopen(req, timeout=timeout)) as r:
                code = getattr(r, "status", 200)
                new_url = r.geturl()
                if 200 <= code < 300:
                    return True, code, new_url, "ok"
                if 300 <= code < 400:
                    current = new_url
                    seen += 1
                    continue
                if method == "HEAD" and code in (400, 401, 403, 405, 501):
                    method = "GET"
                    continue
                return False, code, new_url, f"http_{code}"
        except Exception as e:
            if method == "HEAD":
                method = "GET"
                continue
            return False, None, None, type(e).__name__
    return False, None, current, "redirect_loop"

def slugify_heading(text: str) -> str:
    text = unescape(text)
    text = text.strip().lower()
    text = PUNCT_RE.sub("", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text

def extract_headings(md_text: str) -> List[str]:
    slugs = []
    for ln in md_text.splitlines():
        m = HEADING_RE.match(ln)
        if m:
            slugs.append(slugify_heading(m.group("text")))
    return slugs

def split_anchor(u: str) -> Tuple[str, Optional[str]]:
    parts = u.split("#", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], None

def extract_links(md_text: str) -> List[Tuple[str, int]]:
    links: List[Tuple[str, int]] = []
    for i, line in enumerate(md_text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            url = m.group("md") or m.group("angle") or m.group("bare")
            if not url:
                continue
            links.append((url.strip(), i))
    return links

def should_ignore(path: Path, patterns: List[str]) -> bool:
    from fnmatch import fnmatch
    s = str(path.as_posix())
    return any(fnmatch(s, pat) for pat in patterns)

# --------------------------- Cache ---------------------------

@dataclass
class Cache:
    path: Optional[Path] = None
    max_age: int = 86400  # seconds
    data: Dict[str, Dict] = field(default_factory=dict)

    def load(self):
        if self.path and self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {}

    def save(self):
        if self.path:
            try:
                self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

    def get(self, url: str):
        rec = self.data.get(url)
        if not rec:
            return None
        if time.time() - rec.get("_ts", 0) > self.max_age:
            return None
        return rec

    def put(self, url: str, ok: bool, code: Optional[int], final_url: Optional[str], reason: str):
        self.data[url] = {"ok": ok, "code": code, "final": final_url, "reason": reason, "_ts": time.time()}

# --------------------------- Core checking ---------------------------

def check_external(url: str, timeout: float, cache: Cache) -> Tuple[bool, Optional[int], Optional[str], str]:
    cached = cache.get(url)
    if cached:
        return cached["ok"], cached.get("code"), cached.get("final"), "cached:" + str(cached.get("reason"))
    ok, code, final, reason = http_ok(url, timeout=timeout)
    cache.put(url, ok, code, final, reason)
    return ok, code, final, reason

def check_internal(md_path: Path, url: str) -> Tuple[bool, str]:
    # url may be "other.md#section" or "#section" or "dir/file.md"
    target, anchor = split_anchor(url)
    if target == "":
        # in-page anchor
        anchor = anchor or ""
        slugs = extract_headings(md_path.read_text(encoding="utf-8", errors="ignore"))
        if anchor and slugify_heading(anchor) not in slugs:
            return False, f"missing_anchor: #{anchor}"
        return True, "ok"
    tgt = (md_path.parent / target).resolve()
    if not tgt.exists():
        return False, "missing_relative_path"
    if anchor:
        try:
            slugs = extract_headings(tgt.read_text(encoding="utf-8", errors="ignore"))
            if slugify_heading(anchor) not in slugs:
                return False, f"missing_anchor: #{anchor}"
        except Exception:
            return False, "unreadable_target_for_anchor_check"
    return True, "ok"

# --------------------------- Runner ---------------------------

def process_file(p: Path, verify_rel: bool, timeout: float, external_only: bool,
                 allow_hosts: List[str], deny_hosts: List[str], cache: Cache) -> List[Finding]:
    findings: List[Finding] = []
    txt = p.read_text(encoding="utf-8", errors="ignore")
    for raw_url, line in extract_links(txt):
        url = normalize_url(raw_url)
        u = urlparse(url)

        # Schemes
        if u.scheme in FORBIDDEN_SCHEMES:
            findings.append(Finding(str(p), line, url, "external", "error", "forbidden_scheme"))
            continue
        if u.scheme in SKIP_SCHEMES:
            findings.append(Finding(str(p), line, url, "external", "skip", "skipped_scheme"))
            continue

        # External
        if u.scheme in ("http", "https"):
            host = (u.hostname or "").lower()
            if deny_hosts and any(host.endswith(d) for d in deny_hosts):
                findings.append(Finding(str(p), line, url, "external", "error", "denied_host"))
                continue
            if allow_hosts and not any(host.endswith(a) for a in allow_hosts):
                findings.append(Finding(str(p), line, url, "external", "warning", "not_in_allowlist"))
            if is_private_host(host):
                findings.append(Finding(str(p), line, url, "external", "error", "private_or_localhost"))
                continue
            ok, code, final_url, reason = check_external(url, timeout=timeout, cache=cache)
            status = "ok" if ok else ("warning" if code == 429 else "error")
            findings.append(Finding(str(p), line, url, "external", status, reason, code, final_url))
            continue

        # Internal (relative) link
        if not external_only:
            ok, reason = check_internal(p, url)
            findings.append(Finding(str(p), line, url, "internal", "ok" if ok else "error", reason))
    return findings

def render_text(findings: List[Finding]) -> str:
    lines: List[str] = []
    errs = warns = oks = 0
    for f in findings:
        tag = f.status.upper()
        if f.status == "error": errs += 1
        elif f.status == "warning": warns += 1
        elif f.status == "ok": oks += 1
        code = f"http={f.http_code}" if f.http_code is not None else ""
        lines.append(f"[{tag}] {f.path}:{f.line} -> {f.url} {code} {('- ' + f.reason) if f.reason else ''}")
    lines.append(f"\nSummary: ok={oks} warnings={warns} errors={errs}")
    return "\n".join(lines)

def render_json(findings: List[Finding]) -> str:
    return json.dumps([dataclasses.asdict(f) for f in findings], ensure_ascii=False, indent=2)

def main() -> int:
    ap = argparse.ArgumentParser(description="QuietWire - Markdown Link Checker")
    ap.add_argument("--root", default=".", help="Repo root")
    ap.add_argument("--glob", action="append", default=DEFAULT_GLOBS, help="Glob(s) to scan")
    ap.add_argument("--ignore", action="append", default=DEFAULT_IGNORES, help="Ignore patterns (fnmatch)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument("--no-verify-rel", action="store_true")
    ap.add_argument("--external-only", action="store_true")
    ap.add_argument("--allow-host", action="append", default=[], help="Allow host suffix (may repeat)")
    ap.add_argument("--deny-host", action="append", default=[], help="Deny host suffix (may repeat)")
    ap.add_argument("--format", choices=["text","json"], default="text")
    ap.add_argument("--report", default="-", help="Output path or '-' for stdout")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    ap.add_argument("--cache", default=".linkcheck-cache.json")
    ap.add_argument("--max-age", type=int, default=86400, help="Cache max age seconds")
    args = ap.parse_args()

    root = Path(args.root)
    cache = Cache(Path(args.cache) if args.cache else None, args.max_age)
    cache.load()

    # Gather files
    files: List[Path] = []
    for g in args.glob:
        files.extend([p for p in root.glob(g) if p.is_file()])
    files = [p for p in files if not should_ignore(p, args.ignore)]

    # Process concurrently
    all_findings: List[Finding] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = []
        for p in files:
            futs.append(ex.submit(process_file, p, not args.no_verify_rel, args.timeout,
                                  args.external_only, args.allow_host, args.deny_host, cache))
        for fut in as_completed(futs):
            all_findings.extend(fut.result())

    cache.save()

    # Emit GHA annotations
    errors = warnings = 0
    for f in all_findings:
        if f.status == "error":
            errors += 1
            gha("error", Path(f.path), f.line, f"{f.url} — {f.reason}")
        elif f.status == "warning":
            warnings += 1
            gha("warning", Path(f.path), f.line, f"{f.url} — {f.reason}")

    # Render report
    out = render_json(all_findings) if args.format == "json" else render_text(findings=all_findings)
    if args.report == "-" or not args.report:
        print(out)
    else:
        Path(args.report).write_text(out, encoding="utf-8")
        print(f"Report written to {args.report}")

    if errors or (args.strict and warnings):
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())