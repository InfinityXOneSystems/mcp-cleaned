import os
from typing import Any, Dict

try:
    from google.cloud import bigquery
except Exception:
    bigquery = None


class BigQueryAdapter:
    def __init__(self, client=None, dataset=None, table=None):
        if client:
            self.client = client
        elif bigquery:
            self.client = bigquery.Client()
        else:
            self.client = None
        self.dataset = dataset or os.getenv("BQ_DATASET")
        self.table = table or os.getenv("BQ_TABLE")

    def insert_record(self, record: Dict[str, Any]):
        if not self.client:
            # fallback: local append
            path = os.getenv("BQ_LOCAL", "crawler/output/bq_local.jsonl")
            import json

            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            return
        table_ref = f"{self.client.project}.{self.dataset}.{self.table}"
        errors = self.client.insert_rows_json(table_ref, [record])
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors}")
