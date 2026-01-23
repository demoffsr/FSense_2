"""
Pipeline Orchestrator - v0.3.0

Manages the fixed execution order of all agents.
Enhanced with beautiful console logging for visibility.

Agent Execution Order (FIXED):
1. FIA  → Flower Intent Agent
2. EIA  → Emotion Intelligence Agent
3. RIL  → Relationship Intelligence Layer
4. FMRA → Flower Matching & Ranking Agent
5. CIA  → Context Intensity Agent
6. AITB → Adaptive Intelligence & Tone Builder
7. RFFA → Risk & Fit Assessment Agent
8. CRI  → Cultural & Regional Intelligence
9. SRFL → Self-Reflection Layer
10. SFA → Symbolic Flower Agent (FINAL ASSEMBLER)
"""

from typing import Optional
import logging
import time

from backend.pipeline.context import PipelineContext
from backend.agents.base import BaseAgent
from backend.core.console_logger import get_console_logger

# Agent adapter imports (all are placeholders in v0.0.1)
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


class PipelineOrchestrator:
    """
    Orchestrates the sequential execution of all agents.
    
    In v0.0.1:
    - Fixed order, no dynamic routing
    - Synchronous execution only
    - Basic error handling (log and continue)
    
    TODO v0.1.0:
    - Add async execution support
    - Add parallel execution for independent agents
    - Add circuit breaker pattern
    - Add retry logic per agent
    """
    
    def __init__(self) -> None:
        """Initialize orchestrator with all agent adapters."""
        
        # FIXED EXECUTION ORDER - DO NOT MODIFY
        self._agents: list[BaseAgent] = [
            FIAAdapter(),   # 1. Intent Analysis
            EIAAdapter(),   # 2. Emotion Intelligence
            RILAdapter(),   # 3. Relationship Intelligence
            FMRAAdapter(),  # 4. Flower Matching & Ranking
            CIAAdapter(),   # 5. Context Intensity
            AITBAdapter(),  # 6. Adaptive Tone Building
            RFFAAdapter(),  # 7. Risk & Fit Assessment
            CRIAdapter(),   # 8. Cultural Intelligence
            SRFLAdapter(),  # 9. Self-Reflection
            SFAAdapter(),   # 10. FINAL ASSEMBLY (UI Payload)
        ]
    
    @property
    def agent_names(self) -> list[str]:
        """Get ordered list of agent names."""
        return [agent.name for agent in self._agents]
    
    def run(self, ctx: PipelineContext) -> PipelineContext:
        """
        Execute all agents in fixed order.

        Args:
            ctx: Pipeline context with user input and priors

        Returns:
            Same context object, mutated with all agent outputs
        """
        console = get_console_logger()
        start_time = time.time()

        # Beautiful console output
        console.pipeline_start(ctx.request_id, ctx.user_input, ctx.region)

        logger.info(f"Pipeline started: request_id={ctx.request_id}")

        total_agents = len(self._agents)
        for idx, agent in enumerate(self._agents, 1):
            self._execute_agent(agent, ctx, step=idx, total=total_agents)

        total_time = time.time() - start_time
        success = len(ctx.errors) == 0

        console.pipeline_end(ctx.request_id, success, total_time)
        logger.info(f"Pipeline completed: request_id={ctx.request_id}, time={total_time:.2f}s")

        return ctx
    
    def _execute_agent(self, agent: BaseAgent, ctx: PipelineContext, step: int, total: int) -> None:
        """
        Execute a single agent with timing and error handling.

        Args:
            agent: The agent to execute
            ctx: Pipeline context
            step: Current step number
            total: Total number of steps
        """
        agent_name = agent.name
        console = get_console_logger()

        try:
            console.agent_start(agent_name, step, total)
            logger.debug(f"Starting agent: {agent_name}")
            ctx.start_timing(agent_name)

            agent.run(ctx)

            ctx.end_timing(agent_name, status="completed")
            console.agent_end(agent_name, status="completed")
            logger.debug(f"Completed agent: {agent_name}")

        except Exception as e:
            ctx.end_timing(agent_name, status="failed")
            error_msg = f"{str(e)}"
            ctx.add_error(error_msg)
            console.agent_error(agent_name, error_msg)
            logger.error(f"Agent {agent_name} failed: {error_msg}", exc_info=True)

            # Continue despite errors (graceful degradation)


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
