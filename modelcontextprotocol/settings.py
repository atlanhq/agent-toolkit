"""Configuration settings for the application."""

from typing import Optional
from pydantic_settings import BaseSettings
from version import __version__ as MCP_VERSION


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ATLAN_BASE_URL: str
    ATLAN_API_KEY: str
    ATLAN_AGENT_ID: str = "NA"
    ATLAN_AGENT: str = "atlan-mcp"
    ATLAN_MCP_USER_AGENT: str = f"Atlan MCP Server {MCP_VERSION}"
    MCP_TRANSPORT: str = "stdio"
    MCP_HOST: str = "0.0.0.0"
    MCP_PORT: int = 8000
    MCP_PATH: str = "/"
    # Feature flag: the Context Studio-backed context tools (get_context_tool /
    # get_metric_tool). Default OFF — they need a deployed Context Studio backend
    # (APP_SEMANTIC_EVALS_BASE_URL) and a seeded context glossary on the tenant; on a server
    # without those the tools would only ever error. When off they are fed into the existing
    # ToolRestrictionMiddleware, so they are hidden from tool listings and blocked from calls.
    ENABLE_CONTEXT_TOOLS: bool = False

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


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the singleton Settings instance.
    Loads settings once from environment/file and reuses the instance.

    Returns:
        Settings: The singleton settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
