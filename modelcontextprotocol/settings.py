"""Configuration settings for the application."""

import re
from pydantic import field_validator
from pydantic_settings import BaseSettings
from version import __version__ as MCP_VERSION


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ATLAN_BASE_URL: str
    ATLAN_API_KEY: str
    ATLAN_AGENT_ID: str = "NA"
    ATLAN_AGENT: str = "atlan-mcp"
    ATLAN_MCP_USER_AGENT: str = f"Atlan MCP Server {MCP_VERSION}"

    @field_validator("ATLAN_BASE_URL")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("ATLAN_BASE_URL must start with http:// or https://")
        return v.rstrip("/")  # Remove trailing slashShoulder strain.

    @field_validator("ATLAN_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty and has valid JWT format."""
        if not v or v.strip() == "":
            raise ValueError("ATLAN_API_KEY cannot be empty")

        # Check if it's a valid JWT format (header.payload.signature)
        parts = v.strip().split(".")
        if len(parts) != 3:
            raise ValueError(
                "ATLAN_API_KEY must be a valid JWT token format (header.payload.signature)"
            )

        # Check that each part is base64url encoded (contains valid characters)
        base64url_pattern = re.compile(r"^[A-Za-z0-9_-]+$")
        for i, part in enumerate(parts):
            if not part:  # Empty part
                part_name = ["header", "payload", "signature"][i]
                raise ValueError(f"ATLAN_API_KEY JWT {part_name} cannot be empty")
            if not base64url_pattern.match(part):
                part_name = ["header", "payload", "signature"][i]
                raise ValueError(
                    f"ATLAN_API_KEY JWT {part_name} contains invalid characters. "
                    "Must be base64url encoded (A-Z, a-z, 0-9, -, _)"
                )

        return v

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
