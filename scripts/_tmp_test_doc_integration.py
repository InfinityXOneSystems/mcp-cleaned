from integrations import doc_evolution_integration as dei

print("DOC_EV_FILE:", getattr(dei, "DOC_EV_FILE", None))
res = dei.ingest_document(
    "landing_pages/index.html",
    {"doc_id": "landing_index", "summary": "test ingest", "author": "tester"},
)
print("INGEST RESULT:", res)
res2 = dei.sync_documents("local")
print("SYNC RESULT:", res2)
