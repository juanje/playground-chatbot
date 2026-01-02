"""Response models for toolbox.

Define structured responses that the agent returns.
The supervisor uses these to understand agent output.

BaseAgentResponse already includes:
- response_text: str - Human-readable response
- tools_used: list[str] - Tools that were called

Add your own fields for domain-specific data.
"""

# Uncomment these imports when adding custom fields:
# from typing import Optional
# from pydantic import Field

from macsdk.core import BaseAgentResponse

AgentResponse = BaseAgentResponse
