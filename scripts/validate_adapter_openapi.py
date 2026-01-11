import asyncio
import importlib
import json

m = importlib.import_module("mcp_http_adapter")
print("imported mcp_http_adapter")
r = asyncio.run(m.openapi())
if hasattr(r, "body"):
    obj = json.loads(r.body)
    print("openapi keys:", list(obj.keys()))
    print("paths count:", len(obj.get("paths", {})))
else:
    print("unexpected response type", type(r))
