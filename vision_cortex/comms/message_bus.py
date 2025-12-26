"""In-process Pub/Sub bus with basic observability and error isolation."""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional


class MessageBus:
    def __init__(self, name: str = "vision_cortex") -> None:
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._logger = logging.getLogger(f"vision_cortex.bus.{name}")
        self._middlewares: List[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = []

    def add_middleware(self, middleware: Callable[[str, Dict[str, Any]], Dict[str, Any]]) -> None:
        """Register middleware that can enrich or filter payloads."""
        with self._lock:
            self._middlewares.append(middleware)

    def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        enriched = payload
        with self._lock:
            middlewares = list(self._middlewares)
            subscribers = list(self._subscribers.get(topic, []))

        for mw in middlewares:
            try:
                enriched = mw(topic, enriched)
            except Exception as exc:  # middleware failure should not block publish
                self._logger.warning("Middleware failure on topic %s: %s", topic, exc)
                continue

        for handler in subscribers:
            try:
                handler(enriched)
            except Exception as exc:
                self._logger.error("Subscriber failure on topic %s: %s", topic, exc)
                continue

    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        with self._lock:
            self._subscribers[topic].append(handler)

    def topics(self) -> List[str]:
        with self._lock:
            return list(self._subscribers.keys())
