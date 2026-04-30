---
name: b2b-vendor-customer-mapping
description: Map public B2B vendor-to-customer relationships from vendor websites. Use when Codex needs to crawl vendor domains, discover sitemaps and customer-surface URLs, screen URLs with heuristics or Ollama, extract named customers and customer logos, browser-verify evidence, build vendor-customer and customer-vendor maps, or create review queues for uncertain B2B customer evidence across any industry.
---

# B2B Vendor Customer Mapping

Use this skill to produce a proof-linked public customer map for a list of B2B vendors.

The goal is not to prove a vendor's complete customer universe. The goal is to extract public evidence from vendor-controlled websites and separate verified relationships from review candidates.

## Input

Start from a CSV with at least:

```csv
vendor_slug,vendor_name,vendor_domain
acme,Acme Software,https://www.acme.com
```

Normalize vendor domains before crawling. Remove obvious non-vendors, directories, marketplaces, consumer apps, or wrong-entity domains before calling the output final.

## Pipeline

Run the stages in order. Keep every intermediate file; do not overwrite final outputs without creating a new version suffix.

1. Discover URLs
   - Fetch homepage, `robots.txt`, sitemap indexes, nested sitemaps, and common customer paths.
   - Preserve all discovered URLs before canonicalization.
   - Keep dropped canonical/locale variants in an audit file if deduping.

2. Build customer-surface queue
   - Score URLs for customer evidence likelihood.
   - Prioritize paths and titles containing: `customers`, `clients`, `case-studies`, `customer-stories`, `success-stories`, `references`, `testimonials`, `press-releases`, `news`, `partners`.
   - Treat press releases and acquisition/customer-announcement pages as first-class evidence surfaces.

3. Optional Ollama URL screen
   - Use a local or cloud Ollama model to classify URL likelihood when the sitemap has many ambiguous URLs.
   - Save raw model output and parsed rows.
   - Do not trust model output as final evidence; use it to decide what to fetch/browser-check.

4. Extract named customer evidence
   - Static HTML first.
   - Use page title, H1/H2, JSON-LD, article metadata, and URL slug.
   - Browser-rendered extraction is required for JS-rendered customer pages, logo carousels, and blocked static fetches.

5. Extract logo candidates
   - Extract `img`, `source/srcset`, SVG `image`, and linked image assets.
   - Use `alt`, `title`, filename, surrounding page context, and customer-surface URL context.
   - Reject UI icons, awards, author photos, ebook covers, stock illustrations, vendor self-logos, and generic topic images.

6. Browser QA
   - Named evidence is verified when the evidence page loads and the customer name is visible or strongly token-matched.
   - Logo evidence is verified when the logo asset loads, appears or is referenced on the evidence page, and asset metadata or page context supports the customer name.
   - Never merge unverified rows into the confirmed map. Put them in review queues.

7. Consolidate
   - Produce a final verified vendor-customer pair file.
   - Produce a full overlay file with QA statuses.
   - Produce a reverse customer-vendor map.
   - Produce vendor coverage: verified evidence, review-only candidates, no public evidence found.

## Scripts

Run scripts from the repository root:

```bash
python3 scripts/discover_sitemaps.py --vendors examples/input_vendors.csv --out data/discovered_urls.csv --coverage data/discovery_coverage.csv
python3 scripts/build_url_surface_queue.py --urls data/discovered_urls.csv --out data/customer_surface_queue.csv
python3 scripts/extract_named_customers.py --queue data/customer_surface_queue.csv --out data/named_customer_candidates.csv
python3 scripts/extract_logo_candidates.py --queue data/customer_surface_queue.csv --out data/logo_candidates.csv
python3 scripts/browser_qa_named_evidence.py --input data/named_customer_candidates.csv --out data/named_customer_qa.csv
python3 scripts/browser_qa_logo_evidence.py --input data/logo_candidates.csv --out data/logo_qa.csv
python3 scripts/consolidate_vendor_customer_map.py --named-qa data/named_customer_qa.csv --logo-qa data/logo_qa.csv --out data/final_vendor_customer_pairs.csv --overlay data/final_overlay.csv
python3 scripts/build_reverse_customer_vendor_map.py --pairs data/final_vendor_customer_pairs.csv --out data/customer_vendor_reverse_map.csv
```

Use `scripts/llm_screen_urls_ollama.py` between stages 2 and 3 when a vendor has too many ambiguous URLs for heuristic triage alone.

## Confidence Tiers

Use these final statuses:

- `verified_named_customer`: customer name visible or strongly matched on an official vendor evidence page.
- `verified_customer_logo`: customer logo asset loads, appears or is referenced on the evidence page, and name support is present.
- `review_named_customer`: plausible named evidence but not browser-confirmed.
- `review_customer_logo`: plausible logo evidence but not browser-confirmed.
- `blocked_or_unreachable`: evidence could not be checked in browser.
- `rejected_artifact`: UI, award, topic, author, self-logo, ebook, or other non-customer artifact.
- `no_public_customer_evidence_found`: no clean verified or review candidate after the full pipeline.

## Guardrails

- Preserve proof URLs for every relationship.
- Do not collapse subsidiaries into parents unless the user asks for parent-level normalization.
- Do not call review-only candidates confirmed.
- Do not call a vendor a true zero until sitemap coverage, blocked pages, JS-rendered pages, and dropped canonical variants are accounted for.
- Do not treat logo-only rows as confirmed without logo-specific browser QA.
- If the crawl fails on many domains, inspect failure buckets before retrying with a new IP or VPN.

See `references/output_schemas.md`, `references/confidence_tiers.md`, and `references/failure_modes.md` for details.
