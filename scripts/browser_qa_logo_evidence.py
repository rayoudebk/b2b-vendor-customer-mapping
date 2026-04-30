#!/usr/bin/env python3
import argparse
import asyncio
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from common import append_csv, canonical_url, name_supported, read_csv, surface_score


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
    "error",
]


def url_filename_match(target, candidate):
    t = canonical_url(target)
    c = canonical_url(candidate, target)
    if t == c:
        return True
    tb = Path(urlparse(t).path).name.lower()
    cb = Path(urlparse(c).path).name.lower()
    return bool(tb and cb and tb == cb and len(tb) >= 6)


def out_row(row, status, reason="", title="", body="", error=""):
    return {
        "vendor_slug": row.get("vendor_slug", ""),
        "vendor_name": row.get("vendor_name", ""),
        "vendor_domain": row.get("vendor_domain", ""),
        "customer_name": row.get("customer_name", ""),
        "evidence_page_url": row.get("evidence_page_url", ""),
        "evidence_type": "customer_logo",
        "logo_asset_url": row.get("logo_asset_url", ""),
        "qa_status": status,
        "confidence": "verified" if status == "verified_customer_logo" else "review",
        "match_reason": reason,
        "page_title": title,
        "visible_chars": str(len(body or "")),
        "error": error[:500],
    }


async def check_one(context, row):
    page = await context.new_page()
    url = row.get("evidence_page_url", "")
    target = row.get("logo_asset_url", "")
    try:
        resp = await context.request.get(target, timeout=12000, max_redirects=3)
        asset_load_ok = 200 <= resp.status < 300
    except Exception:
        asset_load_ok = False
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(700)
        title = await page.title()
        body = await page.locator("body").inner_text(timeout=5000)
        assets = await page.evaluate(
            """() => {
              const out = [];
              const push = (el, url) => {
                if (!url) return;
                out.push({
                  url,
                  alt: el.getAttribute('alt') || '',
                  title: el.getAttribute('title') || '',
                  aria: el.getAttribute('aria-label') || ''
                });
              };
              document.querySelectorAll('img').forEach(el => {
                push(el, el.currentSrc || el.src || el.getAttribute('src'));
                (el.getAttribute('srcset') || '').split(',').forEach(part => push(el, part.trim().split(/\\s+/)[0]));
              });
              document.querySelectorAll('source').forEach(el => {
                (el.getAttribute('srcset') || '').split(',').forEach(part => push(el, part.trim().split(/\\s+/)[0]));
              });
              return out;
            }"""
        )
        matched = next((a for a in assets if url_filename_match(target, a.get("url", ""))), None)
        alt_title = ""
        if matched:
            alt_title = " ".join([matched.get("alt", ""), matched.get("title", ""), matched.get("aria", "")])
        filename = Path(urlparse(target).path).name
        ok_name, reason = name_supported(row.get("customer_name", ""), [alt_title, filename, target, title, body[:4000]])
        score, _, _ = surface_score(url, title + " " + body[:2000])
        if asset_load_ok and matched and ok_name and score > 0:
            status = "verified_customer_logo"
        elif not asset_load_ok:
            status = "blocked_or_unreachable"
        elif matched:
            status = "review_customer_logo"
        else:
            status = "review_customer_logo"
        return out_row(row, status, reason, title, body)
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
            key = (result["vendor_slug"], result["customer_name"], result["evidence_page_url"], result["logo_asset_url"])
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
