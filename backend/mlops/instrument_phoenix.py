"""
Arize Phoenix instrumentation for LangChain monitoring.

This module provides OpenInference instrumentation for tracing
LangChain agents, chains, and LLM calls using Arize Phoenix.

Note: With OpenInference auto-instrumentation, all LangChain components
(agents, tools, chains, LLMs) are automatically traced without needing
explicit callbacks.
"""

import os
import sys
from typing import Optional
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace as trace_api
from phoenix.otel import register

from utils.config import AppConfig
from utils.logging import logger


_phoenix_initialized = False


def _is_testing() -> bool:
    """Check if we're running in a test environment."""
    return (
        "pytest" in sys.modules
        or "unittest" in sys.modules
        or os.getenv("TESTING") == "true"
        or os.getenv("PYTEST_CURRENT_TEST") is not None
    )


def setup_phoenix_tracing(
    endpoint: Optional[str] = None,
    project_name: Optional[str] = None,
    force: bool = False,
) -> bool:
    """
    Setup Phoenix tracing for LangChain.

    With OpenInference instrumentation, ALL LangChain components are
    automatically traced:
    - Agents and AgentExecutor
    - Tools (all tool calls)
    - Chains (all chain runs)
    - LLMs and Chat models
    - Retrievers and VectorStores
    - Embeddings

    No explicit callbacks needed!

    Args:
        endpoint: Phoenix OTLP endpoint (default: from AppConfig)
        project_name: Project name for Phoenix (default: from AppConfig)
        force: Force setup even in test environment (default: False)

    Returns:
        bool: True if setup successful, False otherwise
    """
    global _phoenix_initialized

    if _phoenix_initialized:
        logger.info("Phoenix tracing already initialized")
        return True

    # Skip tracing in test environment unless forced
    if _is_testing() and not force:
        logger.info("⏭️  Skipping Phoenix tracing (test environment detected)")
        return False

    try:
        endpoint = endpoint or AppConfig.PHOENIX_ENDPOINT
        project_name = project_name or AppConfig.APP_NAME

        logger.info(f"🔥 Setting up Phoenix tracing for: {project_name}")
        logger.info(f"Phoenix endpoint: {endpoint}")

        # Register Phoenix tracer provider
        tracer_provider = register(
            project_name=project_name,
            endpoint=endpoint,
        )

        # Instrument LangChain - this auto-traces EVERYTHING
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        _phoenix_initialized = True
        logger.info("✅ Phoenix tracing setup successfully")
        logger.info(
            "✅ All LangChain components will be auto-traced (agents, tools, chains, LLMs)"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Error setting up Phoenix tracing: {e}")
        return False


def get_phoenix_tracer(name: str = "langchain"):
    """
    Get Phoenix tracer instance.

    Args:
        name: Tracer name

    Returns:
        Tracer instance
    """
    return trace_api.get_tracer(name)


def shutdown_phoenix():
    """Shutdown Phoenix tracing gracefully."""
    global _phoenix_initialized
    if _phoenix_initialized:
        try:
            # Get the tracer provider and shutdown
            tracer_provider = trace_api.get_tracer_provider()
            if hasattr(tracer_provider, "shutdown"):
                tracer_provider.shutdown()
            _phoenix_initialized = False
            logger.info("✅ Phoenix tracing shutdown successfully")
        except Exception as e:
            logger.error(f"❌ Error shutting down Phoenix: {e}")
