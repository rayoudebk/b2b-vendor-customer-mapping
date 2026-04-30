# Prompt Templates

## URL Surface Screen

Return JSON only.

Input: a B2B vendor name, domain, and a list of URLs.

For each URL, classify whether it is likely to contain public customer evidence.

Labels:

- `high`: customer list, client page, customer story, case study, testimonial, named customer press release.
- `medium`: news, blog, resource, integration, partner page, or ambiguous page likely to mention named customers.
- `low`: product, pricing, generic blog, legal, careers, support, login, docs.

Schema:

```json
[
  {
    "url": "https://example.com/customers/acme",
    "likelihood": "high",
    "surface_type": "case_study",
    "reason": "URL path indicates a customer story for a named organization"
  }
]
```

## Named Customer Extraction

Return JSON only.

Input: page URL, title, headings, visible text excerpt, and metadata.

Extract organization names that are customers, clients, users, adopters, or named case-study subjects of the vendor. Reject people, authors, product names, generic phrases, and article titles.

Schema:

```json
[
  {
    "customer_name": "Acme Bank",
    "evidence_type": "case_study",
    "confidence": "high",
    "reason": "Page title and H1 identify Acme Bank as the case-study subject"
  }
]
