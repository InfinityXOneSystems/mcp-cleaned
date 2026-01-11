"""
Performance Delta Tracker — Track Metric Changes Over Time
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(Enum):
    """Types of metrics tracked."""

    LATENCY = "latency"
    ACCURACY = "accuracy"
    CONFIDENCE = "confidence"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CONSENSUS_RATE = "consensus_rate"
    DEBATE_ROUNDS = "debate_rounds"


@dataclass
class MetricSnapshot:
    """Point-in-time metric snapshot."""

    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "context": self.context,
        }


@dataclass
class PerformanceDelta:
    """Change in performance between two snapshots."""

    metric_type: MetricType
    before: float
    after: float
    delta: float
    delta_percent: float
    improvement: bool
    before_timestamp: datetime
    after_timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "improvement": self.improvement,
            "before_timestamp": self.before_timestamp.isoformat(),
            "after_timestamp": self.after_timestamp.isoformat(),
        }


class PerformanceDeltaTracker:
    """
    Tracks performance deltas between system runs.

    Tracks:
    - Latency (lower is better)
    - Accuracy (higher is better)
    - Confidence (higher is better)
    - Throughput (higher is better)
    - Error rate (lower is better)
    - Consensus rate (higher is better)
    """

    # Metrics where lower is better
    LOWER_IS_BETTER = [
        MetricType.LATENCY,
        MetricType.ERROR_RATE,
        MetricType.DEBATE_ROUNDS,
    ]

    def __init__(self):
        self._snapshots: Dict[MetricType, List[MetricSnapshot]] = {
            t: [] for t in MetricType
        }
        self._deltas: List[PerformanceDelta] = []

    def record(self, snapshot: MetricSnapshot) -> None:
        """Record a metric snapshot."""
        self._snapshots[snapshot.metric_type].append(snapshot)

        # Calculate delta if we have previous snapshot
        history = self._snapshots[snapshot.metric_type]
        if len(history) >= 2:
            delta = self._calculate_delta(history[-2], history[-1])
            self._deltas.append(delta)

    def _calculate_delta(
        self, before: MetricSnapshot, after: MetricSnapshot
    ) -> PerformanceDelta:
        """Calculate delta between two snapshots."""
        delta_value = after.value - before.value
        delta_percent = (delta_value / before.value * 100) if before.value != 0 else 0.0

        # Determine if this is an improvement
        if before.metric_type in self.LOWER_IS_BETTER:
            improvement = delta_value < 0
        else:
            improvement = delta_value > 0

        return PerformanceDelta(
            metric_type=before.metric_type,
            before=before.value,
            after=after.value,
            delta=delta_value,
            delta_percent=delta_percent,
            improvement=improvement,
            before_timestamp=before.timestamp,
            after_timestamp=after.timestamp,
        )

    def get_deltas(
        self, metric_type: Optional[MetricType] = None, improvements_only: bool = False
    ) -> List[PerformanceDelta]:
        """Get performance deltas."""
        deltas = self._deltas

        if metric_type:
            deltas = [d for d in deltas if d.metric_type == metric_type]

        if improvements_only:
            deltas = [d for d in deltas if d.improvement]

        return deltas

    def get_latest(self, metric_type: MetricType) -> Optional[MetricSnapshot]:
        """Get latest snapshot for metric type."""
        history = self._snapshots[metric_type]
        return history[-1] if history else None

    def get_trend(self, metric_type: MetricType, window: int = 10) -> Dict[str, Any]:
        """Get trend for metric over recent window."""
        history = self._snapshots[metric_type][-window:]

        if len(history) < 2:
            return {"trend": "insufficient_data", "points": len(history)}

        values = [s.value for s in history]
        avg = sum(values) / len(values)

        # Simple trend detection
        first_half = sum(values[: len(values) // 2]) / (len(values) // 2)
        second_half = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)

        if metric_type in self.LOWER_IS_BETTER:
            if second_half < first_half * 0.95:
                trend = "improving"
            elif second_half > first_half * 1.05:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            if second_half > first_half * 1.05:
                trend = "improving"
            elif second_half < first_half * 0.95:
                trend = "degrading"
            else:
                trend = "stable"

        return {
            "trend": trend,
            "points": len(history),
            "average": avg,
            "first_half_avg": first_half,
            "second_half_avg": second_half,
        }

    def summary(self) -> Dict[str, Any]:
        """Get summary of all tracked metrics."""
        summary = {}

        for metric_type in MetricType:
            history = self._snapshots[metric_type]
            if history:
                values = [s.value for s in history]
                summary[metric_type.value] = {
                    "count": len(history),
                    "latest": values[-1],
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "trend": self.get_trend(metric_type)["trend"],
                }

        return summary
