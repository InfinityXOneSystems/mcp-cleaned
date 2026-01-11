import importlib.util
import pathlib
import sys

repo_root = pathlib.Path(__file__).resolve().parents[1]
module_path = repo_root / "mcp_http_adapter.py"
spec = importlib.util.spec_from_file_location("mcp_http_adapter", str(module_path))
mod = importlib.util.module_from_spec(spec)
sys.modules["mcp_http_adapter"] = mod
spec.loader.exec_module(mod)
print("IMPORT_OK")
print("router_prefix=", getattr(mod.router, "prefix", None))
