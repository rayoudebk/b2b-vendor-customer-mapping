#!/usr/bin/env python3
import argparse
import re

from bs4 import BeautifulSoup

from common import clean_candidate_name, fetch, infer_name_from_slug, read_csv, write_csv


FIELDS = [
    "vendor_slug",
    "vendor_name",
    "vendor_domain",
    "customer_name",
    "evidence_page_url",
    "evidence_type",
    "confidence",
    "extraction_reason",
]


def title_candidates(title, vendor_name):
    parts = re.split(r"\s+[|-]\s+|: ", title or "")
    candidates = []
    if parts:
        candidates.append(parts[0])
    candidates.extend(parts[1:2])
    return [clean_candidate_name(c, vendor_name) for c in candidates]


def evidence_type_for(row):
    st = row.get("surface_type", "")
    url = row.get("url", "").lower()
    if "press" in url or "news" in url:
        return "press_or_news"
    if st:
        return st
    return "named_customer_evidence"


def extract_from_page(row):
    url = row["url"]
    vendor_name = row.get("vendor_name", "")
    try:
        r = fetch(url, timeout=20)
        if r.status_code >= 400:
            return []
    except Exception:
        return []
    soup = BeautifulSoup(r.text, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2"], limit=6)]
    candidates = []
    for c in title_candidates(title, vendor_name):
        if c:
            candidates.append((c, "title_split"))
    for h in headings:
        c = clean_candidate_name(h, vendor_name)
        if c and len(c.split()) <= 6:
            candidates.append((c, "heading"))
    slug_name = clean_candidate_name(infer_name_from_slug(url), vendor_name)
    if slug_name:
        candidates.append((slug_name, "url_slug"))
    seen, out = set(), []
    for name, reason in candidates:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "vendor_slug": row["vendor_slug"],
                "vendor_name": vendor_name,
                "vendor_domain": row.get("vendor_domain", ""),
                "customer_name": name,
                "evidence_page_url": url,
                "evidence_type": evidence_type_for(row),
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
