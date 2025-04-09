"""Configuration settings for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    atlan_base_url: str
    atlan_api_key: str
    atlan_agent_id: str
    atlan_agent: str = "atlan-mcp"

    @property
    def headers(self) -> dict:
        """Get the headers for API requests."""
        return {
            "x-atlan-agent": self.atlan_agent,
            "x-atlan-agent-id": self.atlan_agent_id,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        # Allow case-insensitive environment variables
        case_sensitive = False
