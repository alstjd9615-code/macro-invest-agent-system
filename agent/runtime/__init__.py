"""Agent runtime adapter package.

Exports :class:`~agent.runtime.agent_runtime.AgentRuntime` and supporting
types for convenient top-level imports.
"""

from agent.runtime.agent_runtime import AgentOperation, AgentRuntime, AgentRuntimeResult

__all__ = ["AgentRuntime", "AgentOperation", "AgentRuntimeResult"]
