#!/usr/bin/env python3
import argparse
import asyncio
from collections import Counter

from playwright.async_api import async_playwright

from common import append_csv, name_supported, read_csv, surface_score


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
    "match_reason",
    "page_title",
    "visible_chars",
    "metadata_chars",
    "error",
]


async def extract_logo_metadata(page):
    return await page.evaluate(
        """() => {
            const values = [];
            const add = value => {
                if (value && typeof value === 'string') values.push(value);
            };
            document.querySelectorAll('img, source, [role="img"]').forEach(el => {
                add(el.getAttribute('alt'));
                add(el.getAttribute('title'));
                add(el.getAttribute('aria-label'));
                add(el.getAttribute('src'));
                add(el.getAttribute('srcset'));
                add(el.getAttribute('data-src'));
                add(el.getAttribute('data-srcset'));
            });
            return values.join(' ');
        }"""
    )


def out_row(row, status, reason="", title="", body="", metadata="", error=""):
    return {
        "vendor_slug": row.get("vendor_slug", ""),
        "vendor_name": row.get("vendor_name", ""),
        "vendor_domain": row.get("vendor_domain", ""),
        "customer_name": row.get("customer_name", ""),
        "evidence_page_url": row.get("evidence_page_url", ""),
        "evidence_type": row.get("evidence_type", "named_customer_evidence"),
        "logo_asset_url": "",
        "qa_status": status,
        "confidence": "verified" if status == "verified_named_customer" else "review",
        "match_reason": reason,
        "page_title": title,
        "visible_chars": str(len(body or "")),
        "metadata_chars": str(len(metadata or "")),
        "error": error[:500],
    }


async def check_one(context, row):
    page = await context.new_page()
    url = row.get("evidence_page_url", "")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(700)
        title = await page.title()
        body = await page.locator("body").inner_text(timeout=5000)
        metadata = await extract_logo_metadata(page)
        ok, reason = name_supported(row.get("customer_name", ""), [body, title, url])
        if not ok and metadata:
            score, surface_type, matched_terms = surface_score(url, f"{title} {body[:2000]}")
            meta_ok, meta_reason = name_supported(row.get("customer_name", ""), [metadata, title, url])
            if meta_ok and score > 0:
                ok = True
                reason = f"customer_surface_{surface_type}_logo_metadata:{meta_reason}:{'|'.join(matched_terms)}"
        return out_row(row, "verified_named_customer" if ok else "review_named_customer", reason, title, body, metadata)
    except Exception as e:
        return out_row(row, "blocked_or_unreachable", "browser_error", error=str(e))
    finally:
        await page.close()


async def worker(context, queue, out, done, lock, counters):
    while True:
        try:
            row = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        result = await check_one(context, row)
        async with lock:
            key = (result["vendor_slug"], result["customer_name"], result["evidence_page_url"], result["evidence_type"])
            if key not in done:
                append_csv(out, result, FIELDS)
                done.add(key)
                counters[result["qa_status"]] += 1
        queue.task_done()


async def main_async(args):
    rows = read_csv(args.input)
    if args.limit:
        rows = rows[: args.limit]
    queue = asyncio.Queue()
    for row in rows:
        queue.put_nowait(row)
    done, counters = set(), Counter()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headful)
        context = await browser.new_context(viewport={"width": 1440, "height": 1200})
        lock = asyncio.Lock()
        await asyncio.gather(*[worker(context, queue, args.out, done, lock, counters) for _ in range(args.workers)])
        await context.close()
        await browser.close()
    print(dict(counters))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--headful", action="store_true")
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
