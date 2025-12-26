# Crawler / Scraper Capability Blueprint (Docs Only)

Scope: expand crawler power without changing enforcement, auth, or rate limits. All controls remain external. This spec defines taxonomies, outputs, and routing so auditors can harden and builders can implement.

## Industry Taxonomy (enum)
- finance, real_estate, energy, healthcare, retail, smb_distress, logistics, technology, manufacturing, gov_contracts, education, hospitality

## Source Taxonomy (enum)
- web, news, filings, sec, courts, patents, forums, social, job_postings, alt_data, feeds, sitemaps, apis

## Output Routing (Firestore collections)
- `crawl_events`: lifecycle events per job/url (status, timings, http meta)
- `crawl_documents`: raw or normalized content blobs with metadata
- `crawl_extractions`: structured fields/entities from rules or models
- `crawl_previews`: safe snippets and thumbnails for UI

All writes include: `session_hash`, `job_id`, `source_type`, `industry_tags[]`, `created_at`.

## Demo-Safe Mode (non-enforcing contract)
- Required flag: `demo_safe = true` in job config
- Redaction fields: `pii_redacted = true`, `content_hash` present, and `preview_only = true` when configured
- Document payloads in demo may include:
  - `content_preview` (<= N chars), `content_hash`, `source_uri`, `title`, `summary`

## Preview Pipeline
- Render `content_preview` and optional `screenshot_uri` under `crawl_previews`.
- Link via `document_ref` to `crawl_documents` when allowed.

## Scaling Knobs (hints; not enforcement)
- `concurrency_hint`, `politeness_delay_ms`, `max_pages`, `depth`, `frequency` (cron or interval)
- Adaptive scheduling hints: recent change scores, source freshness, failure backoff

## Quality Signals
- `fetch_status`, `content_type`, `language`, `dedupe_key`, `checksum_match`, `extraction_coverage`, `extraction_confidence`
