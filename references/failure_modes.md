# Failure Modes

## Sitemap and URL Discovery

- Missing nested sitemap indexes.
- Locale variants dropped during canonicalization.
- Customer pages hidden behind generic paths such as `/resources/`, `/insights/`, `/news/`, or `/press-releases/`.
- Vendor has no sitemap but exposes customer pages through nav links.

Prevention:

- Save raw URLs before dedupe.
- Save canonicalization/dropped-variant audit files.
- Add common fallback paths.
- Treat press releases and news as customer evidence surfaces.

## Static Fetch

- JS-rendered pages return empty HTML.
- Bot protections return soft 403/404 pages.
- PDFs and asset pages need separate handling.

Prevention:

- Separate blocked, empty, and JS-rendered buckets.
- Browser-check high-value evidence URLs.

## Named Extraction

- Article titles can look like customer names.
- Quotes, people, authors, and generic phrases can leak into customer fields.
- Subsidiary and parent names may both be valid, depending on the user's normalization target.

Prevention:

- Keep evidence text and extraction reason.
- Suppress long sentence-like names.
- Normalize parent/subsidiary only as a downstream step.

## Logo Extraction

- UI icons, award badges, topic graphics, ebook covers, and vendor self-logos are common false positives.
- Logo carousels may render only in browser.
- Asset URLs may survive after the page no longer references them.

Prevention:

- Run logo-specific QA.
- Require asset load, evidence-page presence, customer-name support, and customer-surface context before promotion.
