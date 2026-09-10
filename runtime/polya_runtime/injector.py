"""
Polia AI Runtime - Dynamic Context Injector (Phase 19)
Prepares and wraps context packages for non-invasive injection into Hermes Agent messages.
"""

from typing import Dict, List, Optional, Any
from polya_runtime.context_package import ContextPackage

class DynamicContextInjector:
    def __init__(self, max_allowed_tokens: int = 4000):
        self.max_allowed_tokens = max_allowed_tokens

    def inject_system_prompt(self, base_prompt: str, context: ContextPackage) -> str:
        """Append runtime knowledge context to the base system prompt."""
        return (
            f"{base_prompt.strip()}\n\n"
            f"<!-- START POLIA KNOWLEDGE RUNTIME CONTEXT -->\n"
            f"{context.markdown_payload}\n"
            f"<!-- END POLIA KNOWLEDGE RUNTIME CONTEXT -->\n"
        )

    def inject_user_message(self, user_text: str, context: ContextPackage) -> str:
        """Prepend runtime context directly to user message or turn context."""
        return (
            f"<!-- RETRIEVED KNOWLEDGE CONTEXT -->\n"
            f"{context.markdown_payload}\n\n"
            f"<!-- USER INQUIRY -->\n"
            f"{user_text.strip()}"
        )

    def format_as_tool_result(self, context: ContextPackage) -> Dict[str, Any]:
        """Format as a Hermes/MCP tool invocation return payload."""
        return {
            "status": "SUCCESS",
            "active_steps_count": context.active_steps_count,
            "active_sources_count": context.active_sources_count,
            "tokens_estimate": context.total_tokens_estimate,
            "context_markdown": context.markdown_payload,
            "metadata": context.json_payload
        }
