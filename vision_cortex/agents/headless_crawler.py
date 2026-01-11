from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from vision_cortex.agents.base_agent import AgentContext, BaseAgent
from vision_cortex.integration.headless_team import allowed_by_robots, fetch_url


@dataclass
class HeadlessCrawlerAgent(BaseAgent):
    """Simple on-demand headless crawler agent.

    This agent performs a single fetch and returns a compact result. It
    enforces robots.txt unless `no_robots` is passed in the payload and
    `dev_ok` is True in the agent context tags.
    """

    def run_task(
        self, context: AgentContext, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = payload.get("url")
        if not url:
            return {"success": False, "error": "Missing url in payload"}

        no_robots = payload.get("no_robots", False)
        dev_ok = context.tags.get("dev_ok", False)
        if no_robots and not dev_ok:
            return {
                "success": False,
                "error": "no_robots requested but no dev_ok flag present",
            }

        # robots enforcement
        if not no_robots:
            allowed = allowed_by_robots(url)
            if not allowed:
                return {"success": False, "error": "Blocked by robots.txt"}

        # perform fetch
        res = fetch_url(url, timeout=payload.get("timeout", 15))
        out = {
            "success": res.get("status") == "ok",
            "url": url,
            "http_status": res.get("http_status"),
            "content_length": res.get("content_length"),
            "duration": res.get("duration_seconds"),
        }
        if not out["success"]:
            out["error"] = res.get("error", "fetch_failed")
        else:
            out["excerpt"] = res.get("text_excerpt")

        # log event
        self.log_event(
            f"headless fetch {url}",
            context,
            extra={"http_status": out.get("http_status")},
        )
        return out
