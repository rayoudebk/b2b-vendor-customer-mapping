# Confidence Tiers

Use confidence tiers to keep confirmed evidence separate from review candidates.

## Verified

`verified_named_customer`

- Official vendor-controlled evidence page loaded.
- Customer name is visible or strongly token-matched in rendered text, title, URL, or metadata.
- Typical sources: case study, customer story, press release, client page, testimonial.

`verified_customer_logo`

- Official vendor-controlled evidence page loaded.
- Logo asset loads.
- Logo asset is present or referenced on the evidence page.
- Customer name is supported by alt text, title, filename, visible text, URL slug, or page context.

## Review

`review_named_customer`

- Plausible named relationship but not visible after browser QA.
- Keep for human review or retry with a different browser/IP.

`review_customer_logo`

- Logo-like asset but missing one of: asset presence, asset load, customer-name support, customer-surface page context.

`blocked_or_unreachable`

- Evidence URL or logo asset could not be reached.
- Do not convert this to a rejection unless a later retry confirms the page is gone.

## Rejected

`rejected_artifact`

- UI icon, topic image, award badge, blog/ebook cover, author headshot, vendor self-logo, social logo, or other non-customer artifact.

## No Evidence

`no_public_customer_evidence_found`

- Use only after discovery, URL triage, extraction, and browser QA are complete.
