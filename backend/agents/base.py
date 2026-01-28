"""
BaseAgent Interface - v0.0.1

All agents in the pipeline MUST conform to this interface.
This ensures consistent behavior and allows the orchestrator
to execute agents uniformly.

Design Principles:
1. Agents are stateless - all state lives in PipelineContext
2. Agents read from context and write to context
3. Agents do not communicate with each other directly
4. Each agent has a unique name for logging and metrics
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from backend.pipeline.context import PipelineContext


class BaseAgent(ABC):
    """
    Abstract base class for all pipeline agents.
    
    All agent adapters MUST inherit from this class and implement:
    - name: Unique identifier for the agent
    - run(): Execute agent logic and mutate context
    
    Example implementation:
    
        class MyAgentAdapter(BaseAgent):
            name = "MYA"
            
            def run(self, ctx: PipelineContext) -> None:
                # Read from context
                user_input = ctx.user_input
                
                # Do processing...
                result = self._process(user_input)
                
                # Write to context
                ctx.my_output = result
    """
    
    # Unique agent identifier (3-4 characters, uppercase)
    name: ClassVar[str]
    
    @abstractmethod
    def run(self, ctx: PipelineContext) -> None:
        """
        Execute agent logic and mutate the pipeline context.
        
        This method should:
        1. Read required inputs from ctx
        2. Process/transform data
        3. Write outputs to the appropriate ctx section
        
        Args:
            ctx: The pipeline context (mutable)
            
        Returns:
            None - all outputs are written to ctx
            
        Raises:
            Any exception will be caught by orchestrator and logged
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


class AgentError(Exception):
    """Base exception for agent errors."""
    
    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        self.message = message
        super().__init__(f"[{agent_name}] {message}")


class AgentInputError(AgentError):
    """Raised when required input is missing or invalid."""
    pass


class AgentProcessingError(AgentError):
    """Raised when agent processing fails."""
    pass
