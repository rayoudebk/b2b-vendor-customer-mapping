# B2B Vendor Customer Mapping

Open workflow and scripts for mapping public B2B vendor-to-customer relationships from vendor websites.

The project takes a vendor list, discovers website URLs and sitemaps, identifies customer-surface pages, extracts named customers and customer logos, browser-verifies evidence, and exports proof-linked vendor-customer and customer-vendor maps.

It is designed for B2B vendor research across industries. It does not claim to find every customer of every vendor, and it does not prove current commercial status. It maps public evidence found on vendor-controlled websites.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/discover_sitemaps.py --vendors examples/input_vendors.csv --out data/discovered_urls.csv --coverage data/discovery_coverage.csv
python3 scripts/build_url_surface_queue.py --urls data/discovered_urls.csv --out data/customer_surface_queue.csv
python3 scripts/extract_named_customers.py --queue data/customer_surface_queue.csv --out data/named_customer_candidates.csv
python3 scripts/extract_logo_candidates.py --queue data/customer_surface_queue.csv --out data/logo_candidates.csv
python3 scripts/browser_qa_named_evidence.py --input data/named_customer_candidates.csv --out data/named_customer_qa.csv
python3 scripts/browser_qa_logo_evidence.py --input data/logo_candidates.csv --out data/logo_qa.csv
python3 scripts/consolidate_vendor_customer_map.py --named-qa data/named_customer_qa.csv --logo-qa data/logo_qa.csv --out data/final_vendor_customer_pairs.csv --overlay data/final_overlay.csv
python3 scripts/build_reverse_customer_vendor_map.py --pairs data/final_vendor_customer_pairs.csv --out data/customer_vendor_reverse_map.csv
```

For Playwright browser QA, install the browser runtime once:

```bash
python3 -m playwright install chromium
```

## Pipeline

1. Discover sitemaps and likely evidence URLs.
2. Score customer-surface URLs.
3. Optionally screen URLs with Ollama.
4. Extract named customers from pages, titles, headings, metadata, and slugs.
5. Extract logo candidates from customer/client pages.
6. Browser-verify named evidence and logo evidence. Named QA also checks rendered logo/carousel metadata on customer-surface pages, because some sites expose customer names only in `alt`, `title`, `src`, or `srcset` attributes.
7. Consolidate verified pairs and review queues.

Broad logo-alt discovery is useful for rescue work, but should stay in a review queue until page-level validation confirms a customer evidence surface and filters UI icons, awards, partner marks, blog graphics, and vendor self-logos.

## Output

The final pair file contains:

```csv
vendor_slug,vendor_name,vendor_domain,customer_name,evidence_page_url,evidence_type,logo_asset_url,qa_status,confidence
```

The reverse map contains:

```csv
customer_name,vendor_count,vendors,vendor_slugs,evidence_urls,evidence_types
```

## Evidence Statuses

- `verified_named_customer`
- `verified_customer_logo`
- `review_named_customer`
- `review_customer_logo`
- `blocked_or_unreachable`
- `rejected_artifact`
- `no_public_customer_evidence_found`

## Rescue Passes

When a verified map looks complete but a known customer page was missed, rerun the audit in this order:

1. Re-audit existing `review_*` rows with browser-rendered text plus image metadata.
2. Revisit sitemap/customer-surface discovery for generic paths such as `/resources/`, `/news/`, `/success-story`, `/references`, and localized variants.
3. Run broad logo-alt discovery only as a review queue.
4. Promote only rows that pass page-level validation on a vendor-controlled customer evidence page.

## License

MIT
