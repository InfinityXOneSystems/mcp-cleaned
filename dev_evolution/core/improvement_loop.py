"""
Improvement Loop — Continuous System Evolution
Governed by: /mcp/contracts/VISION_CORTEX_LAW.md Article XI

Loop: OBSERVE → HYPOTHESIZE → CHALLENGE → VALIDATE → SYNTHESIZE → PERSIST → REFINE
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class LoopPhase(Enum):
    """Phases of the improvement loop."""

    OBSERVE = "observe"
    HYPOTHESIZE = "hypothesize"
    CHALLENGE = "challenge"
    VALIDATE = "validate"
    SYNTHESIZE = "synthesize"
    PERSIST = "persist"
    REFINE = "refine"


@dataclass
class Observation:
    """System observation for improvement analysis."""

    observation_id: str
    source: str  # agent, metric, external
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


@dataclass
class Hypothesis:
    """Improvement hypothesis."""

    hypothesis_id: str
    observation_id: str
    statement: str
    expected_improvement: float  # 0.0-1.0 scale
    confidence: float
    proposed_by: str  # agent ID
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "observation_id": self.observation_id,
            "statement": self.statement,
            "expected_improvement": self.expected_improvement,
            "confidence": self.confidence,
            "proposed_by": self.proposed_by,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Challenge:
    """Challenge to a hypothesis."""

    challenge_id: str
    hypothesis_id: str
    challenger: str  # agent ID
    argument: str
    counter_evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Synthesis:
    """Synthesized improvement from validated hypothesis."""

    synthesis_id: str
    hypothesis_id: str
    improvement_type: (
        str  # prompt_change, weight_adjustment, threshold_change, architectural
    )
    before_state: Dict[str, Any] = field(default_factory=dict)
    after_state: Dict[str, Any] = field(default_factory=dict)
    approved_by: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ImprovementLoop:
    """
    Orchestrates the continuous improvement cycle.

    Phases:
    1. OBSERVE — Collect system metrics, agent outputs, external signals
    2. HYPOTHESIZE — Generate improvement hypotheses
    3. CHALLENGE — Adversarial testing of hypotheses
    4. VALIDATE — Measure hypothesis against evidence
    5. SYNTHESIZE — Combine validated improvements
    6. PERSIST — Save changes to memory/config
    7. REFINE — Iterate on the process itself

    Questions to ask:
    - What are my assumptions?
    - What would falsify this?
    - What angles am I missing?
    - What's the non-obvious view?
    """

    def __init__(self):
        self.current_phase = LoopPhase.OBSERVE
        self._observations: List[Observation] = []
        self._hypotheses: List[Hypothesis] = []
        self._challenges: List[Challenge] = []
        self._syntheses: List[Synthesis] = []
        self._loop_history: List[Dict[str, Any]] = []

    async def run_cycle(self) -> Dict[str, Any]:
        """Run one complete improvement cycle."""
        cycle_start = datetime.utcnow()
        results = {}

        # Phase 1: OBSERVE
        self.current_phase = LoopPhase.OBSERVE
        observations = await self._observe()
        results["observations"] = len(observations)

        # Phase 2: HYPOTHESIZE
        self.current_phase = LoopPhase.HYPOTHESIZE
        hypotheses = await self._hypothesize(observations)
        results["hypotheses"] = len(hypotheses)

        # Phase 3: CHALLENGE
        self.current_phase = LoopPhase.CHALLENGE
        challenges = await self._challenge(hypotheses)
        results["challenges"] = len(challenges)

        # Phase 4: VALIDATE
        self.current_phase = LoopPhase.VALIDATE
        validated = await self._validate(hypotheses, challenges)
        results["validated"] = len(validated)

        # Phase 5: SYNTHESIZE
        self.current_phase = LoopPhase.SYNTHESIZE
        syntheses = await self._synthesize(validated)
        results["syntheses"] = len(syntheses)

        # Phase 6: PERSIST
        self.current_phase = LoopPhase.PERSIST
        persisted = await self._persist(syntheses)
        results["persisted"] = persisted

        # Phase 7: REFINE
        self.current_phase = LoopPhase.REFINE
        refinements = await self._refine()
        results["refinements"] = refinements

        # Record cycle
        cycle_end = datetime.utcnow()
        cycle_record = {
            "cycle_start": cycle_start.isoformat(),
            "cycle_end": cycle_end.isoformat(),
            "duration_seconds": (cycle_end - cycle_start).total_seconds(),
            "results": results,
        }
        self._loop_history.append(cycle_record)

        return cycle_record

    async def _observe(self) -> List[Observation]:
        """Collect observations from system."""
        # This would be wired to actual system metrics
        return self._observations

    async def _hypothesize(self, observations: List[Observation]) -> List[Hypothesis]:
        """Generate improvement hypotheses from observations."""
        # This would use agent reasoning
        return self._hypotheses

    async def _challenge(self, hypotheses: List[Hypothesis]) -> List[Challenge]:
        """Challenge hypotheses with counter-arguments."""
        # This would involve validator/skeptic agents
        return self._challenges

    async def _validate(
        self, hypotheses: List[Hypothesis], challenges: List[Challenge]
    ) -> List[Hypothesis]:
        """Validate hypotheses against challenges."""
        # Return hypotheses that survived challenges
        challenged_ids = {c.hypothesis_id for c in challenges}
        return [
            h
            for h in hypotheses
            if h.confidence >= 0.7 or h.hypothesis_id not in challenged_ids
        ]

    async def _synthesize(self, validated: List[Hypothesis]) -> List[Synthesis]:
        """Synthesize improvements from validated hypotheses."""
        return self._syntheses

    async def _persist(self, syntheses: List[Synthesis]) -> int:
        """Persist improvements to system."""
        # Would write to memory/config
        return len(syntheses)

    async def _refine(self) -> int:
        """Refine the improvement loop itself."""
        # Meta-improvement
        return 0

    def add_observation(self, observation: Observation) -> None:
        """Add observation for next cycle."""
        self._observations.append(observation)

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Add hypothesis for evaluation."""
        self._hypotheses.append(hypothesis)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get improvement loop history."""
        return self._loop_history.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get current loop status."""
        return {
            "current_phase": self.current_phase.value,
            "observations_pending": len(self._observations),
            "hypotheses_pending": len(self._hypotheses),
            "challenges_pending": len(self._challenges),
            "syntheses_pending": len(self._syntheses),
            "cycles_completed": len(self._loop_history),
        }
