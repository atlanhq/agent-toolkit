"""Configuration settings for the application."""

import requests
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from pydantic_settings import BaseSettings

from version import __version__ as MCP_VERSION


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    ATLAN_BASE_URL: str
    ATLAN_API_KEY: str
    ATLAN_AGENT_ID: str = "NA"
    ATLAN_AGENT: str = "atlan-mcp"
    ATLAN_MCP_USER_AGENT: str = f"Atlan MCP Server {MCP_VERSION}"
    ATLAN_TYPEDEF_API_ENDPOINT: Optional[str] = "/api/meta/types/typedefs/"

    @property
    def headers(self) -> dict:
        """Get the headers for API requests."""
        return {
            "User-Agent": self.ATLAN_MCP_USER_AGENT,
            "X-Atlan-Agent": self.ATLAN_AGENT,
            "X-Atlan-Agent-Id": self.ATLAN_AGENT_ID,
            "X-Atlan-Client-Origin": self.ATLAN_AGENT,
        }

    @staticmethod
    def build_api_url(path: str, query_params: Optional[Dict[str, Any]] = None) -> str:
        current_settings = Settings()
        if not current_settings:
            raise ValueError(
                "Atlan API URL (ATLAN_API_URL) is not configured in settings."
            )

        base_url = current_settings.ATLAN_BASE_URL.rstrip("/")

        if (
            path
            and not path.startswith("/")
            and not base_url.endswith("/")
            and not path.startswith(("http://", "https://"))
        ):
            full_path = f"{base_url}/{path.lstrip('/')}"
        elif path.startswith(("http://", "https://")):
            full_path = path
        else:
            full_path = f"{base_url}{path}"

        if query_params:
            active_query_params = {
                k: v for k, v in query_params.items() if v is not None
            }
            if active_query_params:
                query_string = urlencode(active_query_params)
                return f"{full_path}?{query_string}"
        return full_path

    @staticmethod
    def get_atlan_typedef_api_endpoint(param: str) -> str:
        current_settings = Settings()
        if not current_settings.ATLAN_TYPEDEF_API_ENDPOINT:
            raise ValueError(
                "Default API endpoint for typedefs (api_endpoint) is not configured in settings."
            )

        return Settings.build_api_url(
            path=current_settings.ATLAN_TYPEDEF_API_ENDPOINT,
            query_params={"type": param},
        )

    @staticmethod
    def make_request(url: str) -> Optional[Dict[str, Any]]:
        current_settings = Settings()
        headers = {
            "Authorization": f"Bearer {current_settings.ATLAN_API_KEY}",
            "x-atlan-client-origin": "atlan-search-app",
        }
        try:
            response = requests.get(
                url,
                headers=headers,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to make request to {url}: {response.status_code} {response.text}"
                )
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to make request to {url}: {e}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
        # Allow case-insensitive environment variables
        case_sensitive = False
