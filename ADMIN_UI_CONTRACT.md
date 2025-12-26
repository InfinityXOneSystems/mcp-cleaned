# /admin UI Contract (Crawler Controls)

Specifies dropdown options, field bindings, and events. No backend assumptions or enforcement included.

## Dropdown Options
```json
{
  "industries": [
    {"id": "finance", "label": "Finance"},
    {"id": "real_estate", "label": "Real Estate"},
    {"id": "energy", "label": "Energy"},
    {"id": "healthcare", "label": "Healthcare"},
    {"id": "retail", "label": "Retail"},
    {"id": "smb_distress", "label": "SMB Distress"}
  ],
  "sources": [
    {"id": "web", "label": "Web"},
    {"id": "news", "label": "News"},
    {"id": "filings", "label": "Filings"},
    {"id": "sec", "label": "SEC"},
    {"id": "forums", "label": "Forums"},
    {"id": "social", "label": "Social"}
  ]
}
```

## Field Bindings
- Name: `name`
- Description: `description`
- Seeds: `seeds[]`
- Include patterns: `include_patterns[]`
- Exclude patterns: `exclude_patterns[]`
- Depth: `depth`
- Max pages: `max_pages`
- Politeness (ms): `politeness_delay_ms`
- Concurrency hint: `concurrency_hint`
- Frequency mode: `frequency.mode`
- Cron: `frequency.cron`
- Interval (min): `frequency.interval_minutes`
- Demo Safe: `demo_safe`
- Preview enabled: `preview.enabled`
- Preview max chars: `preview.max_chars`
- Screenshot: `preview.screenshot`

## UI Events
- `config.validate` — validate current form against schema
- `config.save` — persist UI draft (no execution)
- `crawl.start` — request a crawl job using current config
- `crawl.stop` — request stop by `job_id`

## Validation
- Use the JSON Schema in CRAWLER_CONFIG_SCHEMA.md to validate client-side prior to submission.
