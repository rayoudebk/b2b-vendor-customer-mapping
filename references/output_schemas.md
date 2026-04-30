# Output Schemas

## Vendor Input

```csv
vendor_slug,vendor_name,vendor_domain
```

## Discovered URLs

```csv
vendor_slug,vendor_name,vendor_domain,url,discovery_source,http_status,content_type
```

## Customer Surface Queue

```csv
vendor_slug,vendor_name,vendor_domain,url,surface_score,surface_type,matched_terms,queue_reason
```

## Named Customer Candidates

```csv
vendor_slug,vendor_name,vendor_domain,customer_name,evidence_page_url,evidence_type,confidence,extraction_reason
```

## Logo Candidates

```csv
vendor_slug,vendor_name,vendor_domain,customer_name,evidence_page_url,logo_asset_url,asset_alt_title,asset_filename,confidence,extraction_reason
```

## Final Vendor-Customer Pairs

```csv
vendor_slug,vendor_name,vendor_domain,customer_name,evidence_page_url,evidence_type,logo_asset_url,qa_status,confidence
```

## Reverse Customer-Vendor Map

```csv
customer_name,vendor_count,vendors,vendor_slugs,evidence_urls,evidence_types
```
