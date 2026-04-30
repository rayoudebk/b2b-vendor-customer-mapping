#!/usr/bin/env python3
import argparse

from common import read_csv, write_csv


FIELDS = [
    "vendor_slug",
    "vendor_name",
    "vendor_domain",
    "customer_name",
    "evidence_page_url",
    "evidence_type",
    "logo_asset_url",
    "qa_status",
    "confidence",
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--named-qa", required=True)
    p.add_argument("--logo-qa", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--overlay", required=True)
    args = p.parse_args()
    rows = read_csv(args.named_qa) + read_csv(args.logo_qa)
    overlay = []
    final = []
    seen = set()
    for r in rows:
        status = r.get("qa_status", "")
        out = {k: r.get(k, "") for k in FIELDS}
        overlay.append(out)
        if status not in {"verified_named_customer", "verified_customer_logo"}:
            continue
        key = (out["vendor_slug"], out["customer_name"], out["evidence_page_url"], out["logo_asset_url"], out["qa_status"])
        if key in seen:
            continue
        seen.add(key)
        final.append(out)
    write_csv(args.overlay, overlay, FIELDS)
    write_csv(args.out, final, FIELDS)


if __name__ == "__main__":
    main()
