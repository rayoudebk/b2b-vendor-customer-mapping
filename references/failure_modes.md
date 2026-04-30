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
- Customer carousels can expose a short brand name only in rendered logo metadata, while visible text stays empty or generic.

Prevention:

- Keep evidence text and extraction reason.
- Suppress long sentence-like names.
- Normalize parent/subsidiary only as a downstream step.
- In browser QA, inspect image/source `alt`, `title`, `aria-label`, `src`, `srcset`, and lazy-load attributes before rejecting a named candidate.
- Accept short brand tokens from metadata only when the page is a customer evidence surface.

## Logo Extraction

- UI icons, award badges, topic graphics, ebook covers, and vendor self-logos are common false positives.
- Logo carousels may render only in browser.
- Asset URLs may survive after the page no longer references them.
- Broad logo-alt sweeps can recover missed rows, but also pull in UI icons, awards, partners, news graphics, and self-logos.

Prevention:

- Run logo-specific QA.
- Require asset load, evidence-page presence, customer-name support, and customer-surface context before promotion.
- Treat all-vendor logo-alt sweeps as review queues until page-level validation confirms a real customer evidence surface.
