"""
Pipeline Module - v0.0.1

Contains:
- PipelineContext: Single source of truth for all pipeline data
- PipelineOrchestrator: Agent execution order management
- run_flower_chat: Main iOS entrypoint
"""

from backend.pipeline.context import PipelineContext, UserPriors
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.pipeline.runner import run_flower_chat, run_pipeline, run_pipeline_raw

__all__ = [
    # Context
    "PipelineContext",
    "UserPriors",
    # Orchestrator
    "PipelineOrchestrator",
    # Runner (iOS entrypoint)
    "run_flower_chat",
    "run_pipeline",
    "run_pipeline_raw",
]
