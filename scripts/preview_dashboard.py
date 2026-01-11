import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

# Minimal preview helper: starts uvicorn, waits for dashboard, screenshots with pyppeteer.
# Usage: python scripts/preview_dashboard.py

DASH_URL = "http://127.0.0.1:8000/webview/dashboard.html"
OUT_PATH = Path(__file__).resolve().parent.parent / "webview" / "dashboard_preview.png"
UVicorn_CMD = [
    sys.executable,
    "-m",
    "uvicorn",
    "omni_gateway:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
    "--log-level",
    "warning",
]


def wait_for_url(url, timeout=20.0):
    import requests

    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=2.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


async def capture(url, out_path):
    try:
        from pyppeteer import launch
    except Exception:
        print("Missing dependency: install with `pip install pyppeteer requests`")
        return False

    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()
    await page.setViewport({"width": 1400, "height": 900})
    await page.goto(url, {"waitUntil": "networkidle2", "timeout": 20000})
    # optional small delay for dynamic charts to render
    await asyncio.sleep(1.2)
    await page.screenshot({"path": str(out_path), "fullPage": False})
    await browser.close()
    return True


def main():
    # ensure output dir exists
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Starting uvicorn server...")
    proc = subprocess.Popen(
        UVicorn_CMD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(Path(__file__).resolve().parent.parent),
    )

    try:
        ok = wait_for_url(DASH_URL, timeout=25.0)
        if not ok:
            print(
                f"Dashboard not available at {DASH_URL} (timeout). Check that omni_gateway mounts /webview and api_dashboard is included."
            )
            return

        print(f"Dashboard reachable. Capturing screenshot to {OUT_PATH} ...")
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(capture(DASH_URL, OUT_PATH))
        if success:
            print(f"Saved preview: {OUT_PATH}")
            # attempt to open file on Windows/macOS/Linux
            try:
                if sys.platform.startswith("win"):
                    os.startfile(str(OUT_PATH))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(OUT_PATH)])
                else:
                    subprocess.run(["xdg-open", str(OUT_PATH)])
            except Exception:
                pass
        else:
            print(
                "Failed to capture screenshot. Ensure pyppeteer and a working Chromium are available."
            )
    finally:
        print("Stopping uvicorn server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
