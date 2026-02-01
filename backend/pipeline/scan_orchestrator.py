"""
Scan Pipeline Orchestrator - v1.0

Simple 3-agent pipeline for flower scanning:
FID → FSA → SDA

Much simpler than the 10-agent recommendation pipeline.
Expected execution time: ~2-3 seconds.
"""

import logging
import time
from typing import Any, Protocol

from backend.pipeline.scan_context import ScanContext
from backend.core.console_logger import get_console_logger


class ScanAgent(Protocol):
    """Protocol for scan agents."""
    name: str
    def run(self, ctx: ScanContext) -> None: ...

# Agent imports
from backend.agents.adapters.flower_identification_agent import FlowerIdentificationAgent
from backend.agents.adapters.flower_search_agent import FlowerSearchAgent
from backend.agents.adapters.scan_detail_assembler import ScanDetailAssembler

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    """
    Orchestrates the scan pipeline execution.

    Pipeline: FID → FSA → SDA (sequential)

    Unlike the recommendation pipeline, this is intentionally simple
    and sequential since each stage depends on the previous.
    """

    def __init__(self) -> None:
        """Initialize orchestrator with scan agents."""
        self._fid = FlowerIdentificationAgent()
        self._fsa = FlowerSearchAgent()
        self._sda = ScanDetailAssembler()
        self._total_steps = 3

    @property
    def agent_names(self) -> list[str]:
        """Get ordered list of agent names."""
        return ["FID", "FSA", "SDA"]

    def run(self, ctx: ScanContext) -> ScanContext:
        """
        Execute the scan pipeline.

        Args:
            ctx: ScanContext with image and configuration

        Returns:
            ScanContext with quick_payload and detail_payload populated
        """
        console = get_console_logger()
        start_time = time.time()

        console.pipeline_start(ctx.request_id, f"Scan ({ctx.scan_mode})", ctx.region)
        logger.info(f"Scan pipeline started: request_id={ctx.request_id}")

        # Phase 1: Flower Identification (Vision)
        self._execute_agent(self._fid, ctx, step=1)

        # Check for valid identification before continuing
        if not ctx.has_valid_identification():
            logger.warning("FID could not identify flower, skipping FSA")
            # Still run SDA to generate error payload
            self._execute_agent(self._sda, ctx, step=3)
            total_time = time.time() - start_time
            console.pipeline_end(ctx.request_id, False, total_time)
            return ctx

        # Phase 2: Flower Search (Knowledge)
        self._execute_agent(self._fsa, ctx, step=2)

        # Phase 3: Detail Assembly
        self._execute_agent(self._sda, ctx, step=3)

        total_time = time.time() - start_time
        success = len(ctx.errors) == 0

        console.pipeline_end(ctx.request_id, success, total_time)
        logger.info(f"Scan pipeline completed: request_id={ctx.request_id}, time={total_time:.2f}s")

        return ctx

    def _execute_agent(self, agent: ScanAgent, ctx: ScanContext, step: int) -> None:
        """Execute a single agent with timing and error handling."""
        agent_name = agent.name
        console = get_console_logger()

        try:
            console.agent_start(agent_name, step, self._total_steps)
            logger.debug(f"Starting agent: {agent_name}")
            ctx.start_timing(agent_name)

            agent.run(ctx)

            ctx.end_timing(agent_name, status="completed")
            console.agent_end(agent_name, status="completed")
            logger.debug(f"Completed agent: {agent_name}")

        except Exception as e:
            ctx.end_timing(agent_name, status="failed")
            error_msg = str(e)
            ctx.add_error(f"{agent_name}: {error_msg}")
            console.agent_error(agent_name, error_msg)
            logger.error(f"Agent {agent_name} failed: {error_msg}", exc_info=True)


def run_scan(
    image_base64: str,
    scan_mode: str = "single",
    region: str = "US",
) -> dict:
    """
    Run the scan pipeline.

    Args:
        image_base64: Base64-encoded image data
        scan_mode: "single" or "bouquet"
        region: Geographic region for context

    Returns:
        {
            "success": bool,
            "quick": QuickScanPayload dict or None,
            "detail": ScanDetailPayload dict or None,
            "error": str or None
        }
    """
    ctx = ScanContext(
        image_base64=image_base64,
        scan_mode=scan_mode,
        region=region,
    )

    orchestrator = ScanOrchestrator()

    try:
        ctx = orchestrator.run(ctx)

        if ctx.errors:
            return {
                "success": False,
                "quick": ctx.quick_payload,
                "detail": None,
                "error": ctx.errors[0] if ctx.errors else "Unknown error",
            }

        return {
            "success": True,
            "quick": ctx.quick_payload,
            "detail": ctx.detail_payload,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Scan pipeline failed: {e}", exc_info=True)
        return {
            "success": False,
            "quick": None,
            "detail": None,
            "error": str(e),
        }
