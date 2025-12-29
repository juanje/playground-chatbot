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
from typing import Optional
from pydantic import Field


class AgentResponse(BaseAgentResponse):
    """Response model for toolbox.

    Add fields relevant to your agent's domain.
    These help the supervisor understand the structured data.
    """

    # For an API agent:
    api_status: Optional[str] = Field(None, description="Status from the API call")
    data_count: Optional[int] = Field(None, description="Number of items retrieved")

    # For a job/task agent:
    job_id: Optional[str] = Field(None, description="Job or task identifier")
    status: Optional[str] = Field(
        None, description="Job status (pending, running, completed, failed)"
    )
    error_summary: Optional[str] = Field(
        None, description="Summary of any errors encountered"
    )
