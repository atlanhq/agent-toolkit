"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from version import __version__ as MCP_VERSION


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ATLAN_BASE_URL: str
    ATLAN_API_KEY: str
    ATLAN_AGENT_ID: str = "NA"
    ATLAN_AGENT: str = "ext-atlan-mcp"
    ATLAN_MCP_USER_AGENT: str = f"Atlan MCP Server {MCP_VERSION}"

    @property
    def headers(self) -> dict:
        """Get the headers for API requests."""
        return {
            "user-agent": self.ATLAN_MCP_USER_AGENT,
            "x-atlan-agent": self.ATLAN_AGENT,
            "x-atlan-agent-id": "ext-atlan-mcp",
            "x-atlan-client-origin": "ext-atlan-mcp",
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        # Allow case-insensitive environment variables
        case_sensitive = False
