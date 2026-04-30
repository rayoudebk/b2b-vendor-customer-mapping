# Rescue Methodology Case Study

This case study captures the practical lesson from a large 4TPM vendor-customer mapping run.

## Initial Verified Map

- 2,328 retained vendors reviewed.
- 947 vendors had browser-verified customer evidence.
- 10,039 verified vendor-customer pairs.
- 9,100 unique customer names.
- 717 candidates remained review/not-verified.

## Missed Evidence Pattern

A known customer page exposed customer logos in a carousel, but some customer names were only present in rendered image metadata such as `alt`, `title`, `src`, or `srcset`. The named browser QA had checked visible body text, title, and URL, but not rendered image metadata. Short brand tokens were therefore left in review.

## Safe Rescue Sequence

1. Re-audit existing review rows using browser-rendered text plus image/source metadata.
2. Promote only when the candidate appears on a customer evidence surface.
3. Run broad all-vendor logo-alt discovery only as a review queue.
4. Promote broad discoveries only after page-level validation confirms customer-surface context and filters artifacts.

## Observed Outcome

- Review-row re-audit promoted 491 new verified pairs across 171 vendors.
- Broad all-vendor discovery found 54,817 candidate rows across 659 vendors, but two auto-promotion attempts were rolled back as too noisy.
- Page-level validation of the broad discovery promoted 115 additional pairs across 38 vendors.
- Final safe rescue uplift from these stages was 606 inserted verified pairs.

## Rule

Carousel/logo metadata is valid evidence only when tied to an official vendor-controlled customer evidence page. Broad logo-alt matches are discovery signals, not verified customer relationships.
