#!/usr/bin/env python3
import argparse
import json
import subprocess

from common import extract_json_array, read_csv, write_csv


FIELDS = ["vendor_slug", "vendor_name", "vendor_domain", "url", "llm_likelihood", "surface_type", "llm_reason", "raw_model"]


def chunks(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def prompt_for(rows):
    payload = [
        {
            "vendor": r.get("vendor_name", r.get("vendor_slug", "")),
            "domain": r.get("vendor_domain", ""),
            "url": r["url"],
        }
        for r in rows
    ]
    return (
        "Return JSON only. Classify B2B vendor website URLs for likelihood of public customer evidence. "
        "Use high for customer/client lists, case studies, testimonials, customer stories, and named customer press releases. "
        "Use medium for news/resources likely to mention customers. Use low for product, legal, careers, login, docs, generic pages. "
        "Return an array with url, likelihood, surface_type, reason.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="llama3.1:8b")
    p.add_argument("--chunk-size", type=int, default=50)
    args = p.parse_args()
    rows = read_csv(args.queue)
    out = []
    by_url = {r["url"]: r for r in rows}
    for batch in chunks(rows, args.chunk_size):
        proc = subprocess.run(["ollama", "run", args.model, prompt_for(batch)], capture_output=True, text=True)
        raw = proc.stdout if proc.returncode == 0 else proc.stderr
        parsed = extract_json_array(raw)
        for item in parsed:
            url = item.get("url", "")
            base = by_url.get(url, {})
            out.append(
                {
                    "vendor_slug": base.get("vendor_slug", ""),
                    "vendor_name": base.get("vendor_name", ""),
                    "vendor_domain": base.get("vendor_domain", ""),
                    "url": url,
                    "llm_likelihood": item.get("likelihood", ""),
                    "surface_type": item.get("surface_type", ""),
                    "llm_reason": item.get("reason", ""),
                    "raw_model": raw[:2000],
                }
            )
    write_csv(args.out, out, FIELDS)


if __name__ == "__main__":
    main()
