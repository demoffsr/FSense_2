"""
Pipeline Orchestrator - v0.5.0 (RIL Removed)

Manages execution of all agents with PARALLEL optimization.
Independent agents run concurrently to reduce total time.

Execution Strategy:
- Phase 1: FIA + EIA (parallel) - Input analysis
- Phase 1.5: Relationship inference (deterministic, instant)
- Phase 2: FMRA (sequential) - Flower matching
- Phase 3: CIA + AITB + RFFA + CRI (parallel) - Post-matching analysis
- Phase 4: SRFL (sequential) - Self-reflection
- Phase 5: SFA (sequential) - Final assembly

Expected speedup: ~2.3x compared to v0.3.0 (RIL removed = -1 AI call)
"""

from typing import Optional, List
import dataclasses
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
from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
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

    v0.5.0:
    - RIL removed, replaced with deterministic relationship inference
    - Parallel execution for independent agents
    - ~2.3x speedup compared to sequential (one fewer AI call)
    - Thread-safe context access
    """

    def __init__(self) -> None:
        """Initialize orchestrator with all agent adapters."""
        # Create agent instances
        self._via = VIAAdapter()  # Vision Image Analyzer (optional)
        self._fia = FIAAdapter()
        self._eia = EIAAdapter()
        # RIL removed - replaced with deterministic infer_relationship_from_intent()
        self._fmra = FMRAAdapter()
        self._cia = CIAAdapter()
        self._aitb = AITBAdapter()
        self._rffa = RFFAAdapter()
        self._cri = CRIAdapter()
        self._srfl = SRFLAdapter()
        self._sfa = SFAAdapter()

        self._step_counter = 0
        self._step_lock = threading.Lock()
        self._total_steps = 9  # Updated dynamically if VIA runs
        self._executor: Optional[ThreadPoolExecutor] = None  # Shared executor for pipeline run

    @property
    def agent_names(self) -> list[str]:
        """Get ordered list of agent names."""
        return ["VIA", "FIA", "EIA", "FMRA", "CIA", "AITB", "RFFA", "CRI", "SRFL", "SFA"]

    def run(self, ctx: PipelineContext) -> PipelineContext:
        """
        Execute agents with parallel optimization.

        Execution phases:
        1. FIA + EIA (parallel)
        1.5. Relationship inference (deterministic, instant)
        2. FMRA (sequential)
        3. CIA + AITB + RFFA + CRI (parallel)
        4. SRFL (sequential)
        5. SFA (sequential)

        Critical agents (FIA, EIA, FMRA, SFA) will stop the pipeline on failure.
        Non-critical agents log errors but allow continuation.
        """
        console = get_console_logger()
        start_time = time.time()
        self._step_counter = 0

        console.pipeline_start(ctx.request_id, ctx.user_input, ctx.region)
        logger.info(f"Pipeline started (optimized): request_id={ctx.request_id}")

        # Create shared executor for entire pipeline run
        # 4 workers = max parallel batch size (CIA + AITB + RFFA + CRI)
        with ThreadPoolExecutor(max_workers=4) as executor:
            self._executor = executor
            try:
                # Phase 0: Vision analysis (only if image provided)
                if ctx.image_base64:
                    self._total_steps = 10  # Add VIA to step count
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

                # Phase 1.5: Deterministic relationship inference (replaces RIL)
                # No AI call, instant execution
                # Pass EIA data for emotion-aware intensity adjustment
                emotion_data = None
                if ctx.emotions:
                    emotion_data = {
                        "primary_emotion": ctx.emotions.primary_emotion,
                        "emotion_intensity": ctx.emotions.emotion_intensity,
                    }
                ctx.relationship = infer_relationship_from_intent(ctx.intent, emotion_data)
                logger.debug(f"Inferred relationship: {ctx.relationship.relationship_type}")

                # Phase 2: Flower matching
                self._execute_agent(self._fmra, ctx)

                # Phase 3: Post-matching analysis (parallel)
                self._run_parallel(ctx, [self._cia, self._aitb, self._rffa, self._cri])

                # Phase 4: Self-reflection
                self._execute_agent(self._srfl, ctx)

                # Phase 5: Final assembly
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

            finally:
                self._executor = None

        return ctx

    def _run_parallel(self, ctx: PipelineContext, agents: List[BaseAgent]) -> None:
        """Run multiple agents in parallel using shared executor.

        If a critical agent fails, CriticalAgentError is raised after
        all parallel agents complete (to avoid orphaned threads).
        """
        critical_error: Optional[CriticalAgentError] = None

        futures = {
            self._executor.submit(self._execute_agent, agent, ctx, True): agent
            for agent in agents
        }

        for future in as_completed(futures, timeout=AGENT_TIMEOUT_SECONDS * len(agents)):
            agent = futures[future]
            try:
                future.result()
            except CriticalAgentError as e:
                # Capture but don't raise yet - let other agents finish
                critical_error = e
                logger.error(f"Critical agent failed in parallel batch: {e}")
            except Exception as e:
                # Capture unexpected errors with agent context
                error_msg = f"Agent {agent.name} unexpected error: {e}"
                ctx.add_error(error_msg)
                logger.error(f"Parallel agent error: {error_msg}", exc_info=True)

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
            # TODO: iOS must read _preserved_context and re-send priors on follow-up
            "_preserved_context": {
                "priors": dataclasses.asdict(ctx.priors) if ctx.priors else {},
                "region": ctx.region,
                "user_input": ctx.user_input,
            },
        }

    def _execute_agent(
        self,
        agent: BaseAgent,
        ctx: PipelineContext,
        _in_thread: bool = False
    ) -> None:
        """Execute a single agent with timing, timeout, and error handling.

        Args:
            agent: Agent to execute
            ctx: Pipeline context
            _in_thread: If True, agent is already running in executor thread,
                        skip timeout wrapper. Used by _run_parallel.

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

            if _in_thread:
                # Already in executor thread (called from _run_parallel)
                agent.run(ctx)
            else:
                # Sequential call - use shared executor with timeout
                future = self._executor.submit(agent.run, ctx)
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
