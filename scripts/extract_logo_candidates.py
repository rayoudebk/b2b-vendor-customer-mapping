#!/usr/bin/env python3
import argparse
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from common import clean_candidate_name, fetch, normalize_text, read_csv, write_csv


FIELDS = [
    "vendor_slug",
    "vendor_name",
    "vendor_domain",
    "customer_name",
    "evidence_page_url",
    "logo_asset_url",
    "asset_alt_title",
    "asset_filename",
    "confidence",
    "extraction_reason",
]

IMAGE_RE = re.compile(r"\.(svg|png|jpe?g|webp|gif)(\?|#|$)", re.I)
BAD_ASSET_RE = re.compile(r"(icon|sprite|avatar|author|headshot|favicon|placeholder|background|hero|ebook|whitepaper|calendar|award)", re.I)


def asset_name(url):
    name = Path(urlparse(url).path).name
    name = re.sub(r"\.[a-z0-9]{2,5}$", "", name, flags=re.I)
    name = re.sub(r"[-_]+", " ", name)
    name = re.sub(r"\blogo\b", " ", name, flags=re.I)
    return re.sub(r"\s+", " ", name).strip()


def srcset_urls(value):
    for part in (value or "").split(","):
        url = part.strip().split()[0] if part.strip() else ""
        if url:
            yield url


def extract_from_page(row):
    url = row["url"]
    try:
        r = fetch(url, timeout=20)
        if r.status_code >= 400:
            return []
    except Exception:
        return []
    soup = BeautifulSoup(r.text, "lxml")
    out, seen = [], set()
    candidates = []
    for img in soup.find_all(["img", "source"]):
        raw_urls = []
        if img.get("src"):
            raw_urls.append(img.get("src"))
        raw_urls.extend(srcset_urls(img.get("srcset")))
        for raw in raw_urls:
            full = urljoin(url, raw)
            if IMAGE_RE.search(full):
                candidates.append((img, full))
    for el, asset_url in candidates:
        if asset_url in seen or BAD_ASSET_RE.search(asset_url):
            continue
        seen.add(asset_url)
        alt_title = " ".join([el.get("alt", ""), el.get("title", ""), el.get("aria-label", "")]).strip()
        name = clean_candidate_name(alt_title.replace(" logo", "").replace(" Logo", ""), row.get("vendor_name", ""))
        reason = "alt_or_title"
        if not name:
            name = clean_candidate_name(asset_name(asset_url), row.get("vendor_name", ""))
            reason = "asset_filename"
        if not name:
            continue
        if normalize_text(name) in {"logo", "image"}:
            continue
        out.append(
            {
                "vendor_slug": row["vendor_slug"],
                "vendor_name": row.get("vendor_name", ""),
                "vendor_domain": row.get("vendor_domain", ""),
                "customer_name": name,
                "evidence_page_url": url,
                "logo_asset_url": asset_url,
                "asset_alt_title": alt_title,
                "asset_filename": Path(urlparse(asset_url).path).name,
                "confidence": "candidate",
                "extraction_reason": reason,
            }
        )
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()
    rows = read_csv(args.queue)
    if args.limit:
        rows = rows[: args.limit]
    out = []
    for row in rows:
        out.extend(extract_from_page(row))
    write_csv(args.out, out, FIELDS)


if __name__ == "__main__":
    main()
