"""Configuration settings for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ATLAN_BASE_URL: str
    ATLAN_API_KEY: str
    ATLAN_AGENT_ID: str = "NA"
    ATLAN_AGENT: str = "atlan-mcp"

    @property
    def headers(self) -> dict:
        """Get the headers for API requests."""
        return {
            "x-atlan-agent": self.ATLAN_AGENT,
            "x-atlan-agent-id": self.ATLAN_AGENT_ID,
            "x-atlan-client-origin": self.ATLAN_AGENT,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        # Allow case-insensitive environment variables
        case_sensitive = False
