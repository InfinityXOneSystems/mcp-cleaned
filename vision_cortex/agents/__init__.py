"""Agents package for Vision Cortex."""

from vision_cortex.agents.crawler import CrawlerAgent
from vision_cortex.agents.ingestor import IngestorAgent
from vision_cortex.agents.organizer import OrganizerAgent
from vision_cortex.agents.predictor import PredictorAgent
from vision_cortex.agents.visionary import VisionaryAgent
from vision_cortex.agents.strategist import StrategistAgent
from vision_cortex.agents.ceo import CEOAgent
from vision_cortex.agents.validator import ValidatorAgent
from vision_cortex.agents.documentor import DocumentorAgent
from vision_cortex.agents.evolver import EvolverAgent

AGENT_ROLES = [
    "crawler",
    "ingestor",
    "organizer",
    "predictor",
    "visionary",
    "strategist",
    "ceo",
    "validator",
    "documentor",
    "evolver",
]

__all__ = [
    "AGENT_ROLES",
    "CrawlerAgent",
    "IngestorAgent",
    "OrganizerAgent",
    "PredictorAgent",
    "VisionaryAgent",
    "StrategistAgent",
    "CEOAgent",
    "ValidatorAgent",
    "DocumentorAgent",
    "EvolverAgent",
]
