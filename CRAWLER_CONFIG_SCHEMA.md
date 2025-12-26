# Crawler Configuration Schema (Draft 1)

This is a non-enforcing job spec consumed by builders. Auditors can overlay limits without changing this schema.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://infinityx.one/schemas/crawler.job.json",
  "title": "Crawler Job",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "description": {"type": "string"},
    "session_hash": {"type": "string"},
    "industries": {"type": "array", "items": {"type": "string", "enum": [
      "finance","real_estate","energy","healthcare","retail","smb_distress","logistics","technology","manufacturing","gov_contracts","education","hospitality"
    ]}},
    "sources": {"type": "array", "items": {"type": "string", "enum": [
      "web","news","filings","sec","courts","patents","forums","social","job_postings","alt_data","feeds","sitemaps","apis"
    ]}},
    "seeds": {"type": "array", "items": {"type": "string", "format": "uri"}, "minItems": 1},
    "include_patterns": {"type": "array", "items": {"type": "string"}},
    "exclude_patterns": {"type": "array", "items": {"type": "string"}},
    "depth": {"type": "integer", "minimum": 0, "maximum": 5, "default": 1},
    "max_pages": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 500},
    "politeness_delay_ms": {"type": "integer", "minimum": 0, "maximum": 60000, "default": 1000},
    "concurrency_hint": {"type": "integer", "minimum": 1, "maximum": 128, "default": 8},
    "frequency": {
      "type": "object",
      "properties": {
        "mode": {"type": "string", "enum": ["cron","interval"]},
        "cron": {"type": "string", "description": "CRON expr when mode=cron"},
        "interval_minutes": {"type": "integer", "minimum": 5, "maximum": 10080}
      }
    },
    "demo_safe": {"type": "boolean", "const": true},
    "preview": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean", "default": true},
        "max_chars": {"type": "integer", "minimum": 64, "maximum": 4000, "default": 600},
        "screenshot": {"type": "boolean", "default": false},
        "text_only": {"type": "boolean", "default": true}
      }
    },
    "extraction": {
      "type": "object",
      "properties": {
        "rules": {"type": "array", "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "selector": {"type": "string"},
            "attr": {"type": "string"},
            "regex": {"type": "string"}
          },
          "required": ["name","selector"]
        }},
        "llm_assist": {"type": "boolean", "default": false}
      }
    },
    "routing": {
      "type": "object",
      "properties": {
        "events": {"type": "string", "default": "crawl_events"},
        "documents": {"type": "string", "default": "crawl_documents"},
        "extractions": {"type": "string", "default": "crawl_extractions"},
        "previews": {"type": "string", "default": "crawl_previews"}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "tags": {"type": "array", "items": {"type": "string"}},
        "owner": {"type": "string"}
      }
    }
  },
  "required": ["name","session_hash","seeds","demo_safe"]
}
```

## Example (minimal)
```json
{
  "name": "TX Energy Filings Radar",
  "session_hash": "abc123",
  "industries": ["energy"],
  "sources": ["filings","news"],
  "seeds": ["https://www.sec.gov/edgar/searchedgar/companysearch.html"],
  "demo_safe": true
}
```
