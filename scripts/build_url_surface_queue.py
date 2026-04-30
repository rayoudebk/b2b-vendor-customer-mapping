#!/usr/bin/env python3
import argparse

from common import read_csv, surface_score, write_csv


FIELDS = ["vendor_slug", "vendor_name", "vendor_domain", "url", "surface_score", "surface_type", "matched_terms", "queue_reason"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--urls", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--min-score", type=int, default=2)
    p.add_argument("--include-low", action="store_true")
    args = p.parse_args()
    out = []
    for row in read_csv(args.urls):
        score, surface_type, matched = surface_score(row["url"])
        if score >= args.min_score or args.include_low:
            out.append(
                {
                    "vendor_slug": row["vendor_slug"],
                    "vendor_name": row.get("vendor_name", ""),
                    "vendor_domain": row.get("vendor_domain", ""),
                    "url": row["url"],
                    "surface_score": score,
                    "surface_type": surface_type,
                    "matched_terms": " | ".join(matched),
                    "queue_reason": "matched_customer_surface_terms" if matched else "included_low_score",
                }
            )
    out.sort(key=lambda r: (-int(r["surface_score"]), r["vendor_slug"], r["url"]))
    write_csv(args.out, out, FIELDS)


if __name__ == "__main__":
    main()
