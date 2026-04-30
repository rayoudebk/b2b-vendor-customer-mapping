#!/usr/bin/env python3
import argparse
import xml.etree.ElementTree as ET
from collections import deque
from urllib.parse import urljoin

from common import canonical_url, ensure_url, fetch, read_csv, slugify, write_csv


COMMON_PATHS = [
    "/customers",
    "/clients",
    "/case-studies",
    "/customer-stories",
    "/success-stories",
    "/testimonials",
    "/references",
    "/press-releases",
    "/news",
]

SITEMAP_PATHS = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/wp-sitemap.xml", "/sitemap.txt"]


def parse_sitemap(text):
    urls = []
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except Exception:
        return urls
    for el in root.iter():
        if el.tag.lower().endswith("loc") and el.text:
            urls.append(el.text.strip())
    return urls


def robots_sitemaps(base_url):
    try:
        r = fetch(urljoin(base_url + "/", "robots.txt"), timeout=10)
    except Exception:
        return []
    out = []
    for line in r.text.splitlines():
        if line.lower().startswith("sitemap:"):
            out.append(line.split(":", 1)[1].strip())
    return out


def discover_vendor(row, max_sitemaps=50, max_urls=50000):
    vendor_domain = ensure_url(row.get("vendor_domain") or row.get("vendor_website") or row.get("domain"))
    vendor_slug = row.get("vendor_slug") or slugify(row.get("vendor_name") or vendor_domain)
    vendor_name = row.get("vendor_name") or row.get("vendor_name_guess") or vendor_slug
    discovered = []
    seen = set()

    def add(url, source, status="", content_type=""):
        url = canonical_url(url, vendor_domain)
        if not url or url in seen:
            return
        seen.add(url)
        discovered.append(
            {
                "vendor_slug": vendor_slug,
                "vendor_name": vendor_name,
                "vendor_domain": vendor_domain,
                "url": url,
                "discovery_source": source,
                "http_status": status,
                "content_type": content_type,
            }
        )

    add(vendor_domain, "homepage")
    sitemap_queue = deque(robots_sitemaps(vendor_domain) + [urljoin(vendor_domain + "/", p.lstrip("/")) for p in SITEMAP_PATHS])
    sitemap_seen = set()
    sitemap_count = 0
    while sitemap_queue and sitemap_count < max_sitemaps and len(discovered) < max_urls:
        sm = canonical_url(sitemap_queue.popleft(), vendor_domain)
        if sm in sitemap_seen:
            continue
        sitemap_seen.add(sm)
        sitemap_count += 1
        try:
            r = fetch(sm, timeout=20)
        except Exception:
            continue
        if r.status_code >= 400:
            continue
        locs = parse_sitemap(r.text)
        for loc in locs:
            if "sitemap" in loc.lower() and loc.lower().endswith((".xml", ".xml.gz")):
                sitemap_queue.append(loc)
            else:
                add(loc, "sitemap")
                if len(discovered) >= max_urls:
                    break
    for path in COMMON_PATHS:
        url = urljoin(vendor_domain + "/", path.lstrip("/"))
        try:
            r = fetch(url, timeout=10)
            if r.status_code < 500:
                add(url, "common_path", str(r.status_code), r.headers.get("content-type", ""))
        except Exception:
            add(url, "common_path_error")
    coverage = {
        "vendor_slug": vendor_slug,
        "vendor_name": vendor_name,
        "vendor_domain": vendor_domain,
        "discovered_url_count": len(discovered),
        "sitemap_count_checked": sitemap_count,
    }
    return discovered, coverage


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vendors", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--coverage", required=True)
    p.add_argument("--max-sitemaps", type=int, default=50)
    p.add_argument("--max-urls-per-vendor", type=int, default=50000)
    args = p.parse_args()
    all_rows, coverage = [], []
    for row in read_csv(args.vendors):
        rows, cov = discover_vendor(row, args.max_sitemaps, args.max_urls_per_vendor)
        all_rows.extend(rows)
        coverage.append(cov)
    write_csv(args.out, all_rows, ["vendor_slug", "vendor_name", "vendor_domain", "url", "discovery_source", "http_status", "content_type"])
    write_csv(args.coverage, coverage, ["vendor_slug", "vendor_name", "vendor_domain", "discovered_url_count", "sitemap_count_checked"])


if __name__ == "__main__":
    main()
