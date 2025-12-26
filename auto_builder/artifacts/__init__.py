"""
Auto Builder Artifact System
Generates mandatory build artifacts:
- build_plan.json
- execution_log.json
- diff_manifest.json
- validation_report.json
"""

from .artifact_writer import ArtifactWriter

__all__ = ["ArtifactWriter"]
