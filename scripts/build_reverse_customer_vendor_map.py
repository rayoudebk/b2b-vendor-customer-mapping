#!/usr/bin/env python3
import argparse
from collections import defaultdict

from common import read_csv, write_csv


FIELDS = ["customer_name", "vendor_count", "vendors", "vendor_slugs", "evidence_urls", "evidence_types"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pairs", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    grouped = defaultdict(list)
    for row in read_csv(args.pairs):
        grouped[row["customer_name"]].append(row)
    out = []
    for customer, rows in sorted(grouped.items(), key=lambda kv: (-len({r["vendor_slug"] for r in kv[1]}), kv[0].lower())):
        vendor_slugs = list(dict.fromkeys(r["vendor_slug"] for r in rows))
        vendors = list(dict.fromkeys((r.get("vendor_name") or r["vendor_slug"]) for r in rows))
        urls = list(dict.fromkeys(r.get("evidence_page_url", "") for r in rows if r.get("evidence_page_url")))
        types = sorted(set(r.get("qa_status", "") for r in rows))
        out.append(
            {
                "customer_name": customer,
                "vendor_count": len(vendor_slugs),
                "vendors": " | ".join(vendors),
                "vendor_slugs": " | ".join(vendor_slugs),
                "evidence_urls": " | ".join(urls),
                "evidence_types": " | ".join(types),
            }
        )
    write_csv(args.out, out, FIELDS)


if __name__ == "__main__":
    main()
