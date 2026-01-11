import requests

BASE = "http://localhost:8000"


def test_ingest():
    payload = {
        "source": "landing_pages/index.html",
        "metadata": {"source_type": "landing"},
    }
    r = requests.post(BASE + "/admin/doc/ingest", json=payload)
    print("INGEST", r.status_code, r.json())


def test_evolve():
    payload = {"doc_id": "landing_pages/index.html", "strategy": {"rewrite": True}}
    r = requests.post(BASE + "/admin/doc/evolve", json=payload)
    print("EVOLVE", r.status_code, r.json())


def test_sync():
    payload = {"target": "hostinger:/public_html"}
    r = requests.post(BASE + "/admin/doc/sync", json=payload)
    print("SYNC", r.status_code, r.json())


if __name__ == "__main__":
    test_ingest()
    test_evolve()
    test_sync()
