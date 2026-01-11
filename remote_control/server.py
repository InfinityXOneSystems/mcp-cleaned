"""
Remote control lightweight server for secure remote commands to VS Code instance.
Accepts a token and simple command envelopes. For security, default bind to localhost.
"""

import logging
import os
import subprocess

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
app = FastAPI(title="Remote Control Bridge")

AUTH_TOKEN = os.environ.get("REMOTE_CTRL_TOKEN", "dev-token")


class CmdReq(BaseModel):
    command: str
    args: dict = {}


def check_token(req: Request):
    token = req.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    if token.split(" ", 1)[1] != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="invalid token")


@app.post("/command")
async def run_command(payload: CmdReq, request: Request):
    check_token(request)
    cmd = payload.command
    # map allowed commands to safe operations
    allowed = {
        "restart_agents": ["python", "-m", "agents.runner", "--start"],
        "run_tests": ["pytest"],
        "open_file": ["code", "-r", payload.args.get("path", "")],
    }
    if cmd not in allowed:
        raise HTTPException(status_code=400, detail="command not allowed")
    try:
        p = subprocess.Popen(allowed[cmd])
        return {"status": "ok", "pid": p.pid}
    except Exception as e:
        logger.error(f"Command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
