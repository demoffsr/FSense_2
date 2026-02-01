"""
Pipeline Orchestrator - v0.4.0 (Optimized)

Manages execution of all agents with PARALLEL optimization.
Independent agents run concurrently to reduce total time.

Execution Strategy:
- Phase 1: FIA + EIA (parallel) - Input analysis
- Phase 2: RIL (sequential) - Needs intent + emotions
- Phase 3: FMRA (sequential) - Flower matching
- Phase 4: CIA + AITB + RFFA + CRI (parallel) - Post-matching analysis
- Phase 5: SRFL (sequential) - Self-reflection
- Phase 6: SFA (sequential) - Final assembly

Expected speedup: ~2x compared to sequential execution.
"""

from typing import Optional, List
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

from backend.pipeline.context import PipelineContext
from backend.agents.base import BaseAgent
from backend.core.console_logger import get_console_logger

# Agent adapter imports
from backend.agents.adapters.via_adapter import VIAAdapter
from backend.agents.adapters.fia_adapter import FIAAdapter
from backend.agents.adapters.eia_adapter import EIAAdapter
from backend.agents.adapters.ril_adapter import RILAdapter
from backend.agents.adapters.fmra_adapter import FMRAAdapter
from backend.agents.adapters.cia_adapter import CIAAdapter
from backend.agents.adapters.aitb_adapter import AITBAdapter
from backend.agents.adapters.rffa_adapter import RFFAAdapter
from backend.agents.adapters.cri_adapter import CRIAdapter
from backend.agents.adapters.srfl_adapter import SRFLAdapter
from backend.agents.adapters.sfa_adapter import SFAAdapter

logger = logging.getLogger(__name__)

# Agent execution timeout in seconds
AGENT_TIMEOUT_SECONDS = 30

# Critical agents - pipeline cannot continue without these
# FIA: intent is required for all downstream agents
# EIA: emotions are required for flower matching
# FMRA: without flower selection, nothing to present
# SFA: without assembly, no UI payload
CRITICAL_AGENTS = {"FIA", "EIA", "FMRA", "SFA"}


class AgentTimeoutError(Exception):
    """Raised when an agent exceeds the execution timeout."""
    pass


class CriticalAgentError(Exception):
    """Raised when a critical agent fails, stopping the pipeline."""
    pass


class PipelineOrchestrator:
    """
    Orchestrates agent execution with parallel optimization.

    v0.4.0:
    - Parallel execution for independent agents
    - ~2x speedup compared to sequential
    - Thread-safe context access
    """

    def __init__(self) -> None:
        """Initialize orchestrator with all agent adapters."""
        # Create agent instances
        self._via = VIAAdapter()  # Vision Image Analyzer (optional)
        self._fia = FIAAdapter()
        self._eia = EIAAdapter()
        self._ril = RILAdapter()
        self._fmra = FMRAAdapter()
        self._cia = CIAAdapter()
        self._aitb = AITBAdapter()
        self._rffa = RFFAAdapter()
        self._cri = CRIAdapter()
        self._srfl = SRFLAdapter()
        self._sfa = SFAAdapter()

        self._step_counter = 0
        self._step_lock = threading.Lock()
        self._total_steps = 10  # Updated dynamically if VIA runs

    @property
    def agent_names(self) -> list[str]:
        """Get ordered list of agent names."""
        return ["VIA", "FIA", "EIA", "RIL", "FMRA", "CIA", "AITB", "RFFA", "CRI", "SRFL", "SFA"]

    def run(self, ctx: PipelineContext) -> PipelineContext:
        """
        Execute agents with parallel optimization.

        Execution phases:
        1. FIA + EIA (parallel)
        2. RIL (sequential)
        3. FMRA (sequential)
        4. CIA + AITB + RFFA + CRI (parallel)
        5. SRFL (sequential)
        6. SFA (sequential)

        Critical agents (FIA, EIA, FMRA, SFA) will stop the pipeline on failure.
        Non-critical agents log errors but allow continuation.
        """
        console = get_console_logger()
        start_time = time.time()
        self._step_counter = 0

        console.pipeline_start(ctx.request_id, ctx.user_input, ctx.region)
        logger.info(f"Pipeline started (optimized): request_id={ctx.request_id}")

        try:
            # Phase 0: Vision analysis (only if image provided)
            if ctx.image_base64:
                self._total_steps = 11  # Add VIA to step count
                self._execute_agent(self._via, ctx)

                # Check if clarification needed - early exit
                if ctx.vision.needs_clarification:
                    logger.info("Vision analysis needs clarification, returning early")
                    # Build a clarification response instead of full pipeline
                    ctx.ui_payload = self._build_clarification_payload(ctx)
                    total_time = time.time() - start_time
                    console.pipeline_end(ctx.request_id, True, total_time)
                    return ctx

            # Phase 1: Input analysis (parallel)
            self._run_parallel(ctx, [self._fia, self._eia])

            # Phase 2: Relationship analysis (needs intent + emotions)
            self._execute_agent(self._ril, ctx)

            # Phase 3: Flower matching
            self._execute_agent(self._fmra, ctx)

            # Phase 4: Post-matching analysis (parallel)
            self._run_parallel(ctx, [self._cia, self._aitb, self._rffa, self._cri])

            # Phase 5: Self-reflection
            self._execute_agent(self._srfl, ctx)

            # Phase 6: Final assembly
            self._execute_agent(self._sfa, ctx)

            total_time = time.time() - start_time
            success = len(ctx.errors) == 0

            console.pipeline_end(ctx.request_id, success, total_time)
            logger.info(f"Pipeline completed: request_id={ctx.request_id}, time={total_time:.2f}s")

        except CriticalAgentError as e:
            total_time = time.time() - start_time
            ctx.add_error(f"Pipeline aborted: {str(e)}")
            console.pipeline_end(ctx.request_id, False, total_time)
            logger.error(f"Pipeline aborted due to critical agent failure: {e}")

        return ctx

    def _run_parallel(self, ctx: PipelineContext, agents: List[BaseAgent]) -> None:
        """Run multiple agents in parallel using ThreadPoolExecutor.

        If a critical agent fails, CriticalAgentError is raised after
        all parallel agents complete (to avoid orphaned threads).
        """
        critical_error: Optional[CriticalAgentError] = None

        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {
                executor.submit(self._execute_agent, agent, ctx): agent
                for agent in agents
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except CriticalAgentError as e:
                    # Capture but don't raise yet - let other agents finish
                    critical_error = e
                    logger.error(f"Critical agent failed in parallel batch: {e}")
                except Exception as e:
                    logger.error(f"Parallel agent error: {e}")

        # Raise critical error after all agents complete
        if critical_error:
            raise critical_error

    def _build_clarification_payload(self, ctx: PipelineContext) -> dict:
        """Build a clarification response when vision analysis needs user input."""
        # Collect flower options from vision analysis
        options = []
        if ctx.vision.main_flower:
            options.append({
                "name": ctx.vision.main_flower.name,
                "description": f"Main flower detected with {ctx.vision.main_flower.confidence:.0%} confidence"
            })
        for flower in ctx.vision.secondary_flowers[:4]:
            options.append({
                "name": flower.name,
                "description": f"Secondary flower ({flower.color or 'unknown color'})"
            })

        return {
            "type": "clarification",
            "message": ctx.vision.clarification_message or "I see multiple flowers in the image. Which one would you like to know more about?",
            "options": options,
            "bouquet_description": ctx.vision.bouquet_description,
            "request_id": ctx.request_id,
            "pipeline_version": "0.3.0",
        }

    def _execute_agent(self, agent: BaseAgent, ctx: PipelineContext) -> None:
        """Execute a single agent with timing, timeout, and error handling.

        Critical agents (FIA, EIA, FMRA, SFA) will raise CriticalAgentError
        on failure, stopping the pipeline. Non-critical agents log errors
        but allow the pipeline to continue.
        """
        agent_name = agent.name
        console = get_console_logger()
        is_critical = agent_name in CRITICAL_AGENTS

        with self._step_lock:
            self._step_counter += 1
            step = self._step_counter

        try:
            console.agent_start(agent_name, step, self._total_steps)
            logger.debug(f"Starting agent: {agent_name}")
            ctx.start_timing(agent_name)

            # Run agent with timeout to prevent hangs
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(agent.run, ctx)
                try:
                    future.result(timeout=AGENT_TIMEOUT_SECONDS)
                except FuturesTimeoutError:
                    raise AgentTimeoutError(
                        f"Agent {agent_name} timed out after {AGENT_TIMEOUT_SECONDS}s"
                    )

            ctx.end_timing(agent_name, status="completed")
            console.agent_end(agent_name, status="completed")
            logger.debug(f"Completed agent: {agent_name}")

        except AgentTimeoutError as e:
            ctx.end_timing(agent_name, status="timeout")
            error_msg = str(e)
            ctx.add_error(error_msg)
            console.agent_error(agent_name, error_msg)
            logger.error(f"Agent {agent_name} timeout: {error_msg}")
            # Critical agents stop the pipeline
            if is_critical:
                raise CriticalAgentError(f"Critical agent {agent_name} timed out") from e

        except CriticalAgentError:
            # Re-raise critical errors without wrapping
            raise

        except Exception as e:
            ctx.end_timing(agent_name, status="failed")
            error_msg = f"{str(e)}"
            ctx.add_error(error_msg)
            console.agent_error(agent_name, error_msg)
            logger.error(f"Agent {agent_name} failed: {error_msg}", exc_info=True)
            # Critical agents stop the pipeline
            if is_critical:
                raise CriticalAgentError(f"Critical agent {agent_name} failed: {error_msg}") from e


class PipelineOrchestratorBuilder:
    """
    Builder for customizing orchestrator configuration.
    
    TODO v0.1.0:
    - Add agent exclusion
    - Add agent replacement
    - Add custom ordering (if needed)
    """
    
    def __init__(self) -> None:
        self._skip_agents: set[str] = set()
    
    def skip(self, agent_name: str) -> "PipelineOrchestratorBuilder":
        """Mark an agent to be skipped (for testing)."""
        self._skip_agents.add(agent_name)
        return self
    
    def build(self) -> PipelineOrchestrator:
        """Build the orchestrator with current configuration."""
        # TODO: Apply skip configuration
        return PipelineOrchestrator()
