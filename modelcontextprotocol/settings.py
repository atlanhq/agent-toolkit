"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from version import __version__ as MCP_VERSION


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ATLAN_BASE_URL: str
    ATLAN_API_KEY: str
    ATLAN_AGENT_ID: str = "NA"
    ATLAN_AGENT: str = "atlan-mcp"
    ATLAN_MCP_USER_AGENT: str = f"Atlan MCP Server {MCP_VERSION}"

    @property
    def headers(self) -> dict:
        """Get the headers for API requests."""
        return {
            "User-Agent": self.ATLAN_MCP_USER_AGENT,
            "X-Atlan-Agent": self.ATLAN_AGENT,
            "X-Atlan-Agent-Id": self.ATLAN_AGENT_ID,
            "X-Atlan-Client-Origin": self.ATLAN_AGENT,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        # Allow case-insensitive environment variables
        case_sensitive = False
