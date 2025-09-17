"""
LLMS.txt documentation tools for MCP server.
Provides access to llms.txt files and documentation fetching capabilities.
"""

import re
import httpx
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from dataclasses import dataclass


@dataclass
class DocSource:
    """Represents a documentation source with name and llms.txt URL."""

    name: str
    llms_txt_url: str
    allowed_domains: List[str]


class LLMSTxtManager:
    """Manages llms.txt documentation sources and fetching."""

    def __init__(self):
        self.sources: Dict[str, DocSource] = {}
        self.timeout = 30.0  # Increased timeout for documentation fetching
        self.follow_redirects = True  # Allow redirects for documentation URLs
        self._initialize_default_sources()

    def _initialize_default_sources(self):
        """Initialize with default documentation sources."""
        default_sources = [
            DocSource(
                name="Atlan Docs",
                llms_txt_url="https://docs.atlan.com/llms.txt",
                allowed_domains=["docs.atlan.com"],
            )
        ]

        for source in default_sources:
            self.sources[source.name] = source

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all available documentation sources."""
        return [
            {
                "name": source.name,
                "llms_txt_url": source.llms_txt_url,
                "allowed_domains": source.allowed_domains,
            }
            for source in self.sources.values()
        ]

    def _is_domain_allowed(self, url: str, allowed_domains: List[str]) -> bool:
        """Check if URL domain is in allowed domains list."""
        if "*" in allowed_domains:
            return True

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for allowed in allowed_domains:
            if domain == allowed.lower() or domain.endswith("." + allowed.lower()):
                return True

        return False

    async def _fetch_content(self, url: str) -> str:
        """Fetch content from URL with proper error handling."""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, read=self.timeout),
                follow_redirects=self.follow_redirects,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException:
            raise Exception(f"Timeout fetching {url} after {self.timeout}s")
        except httpx.RequestError as e:
            raise Exception(f"Request error fetching {url}: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code} error fetching {url}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error fetching {url}: {e}")

    async def fetch_llms_txt(self, source_name: str) -> Dict[str, Any]:
        """Fetch and parse llms.txt content from a source."""
        if source_name not in self.sources:
            raise Exception(f"Unknown source: {source_name}")

        source = self.sources[source_name]

        try:
            content = await self._fetch_content(source.llms_txt_url)

            # Parse llms.txt content to extract URLs
            lines = content.strip().split("\n")
            urls = []

            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Handle different llms.txt formats
                    if line.startswith("http"):
                        urls.append(line)
                    elif ": " in line and "http" in line:
                        # Format: "Title: URL"
                        parts = line.split(": ", 1)
                        if len(parts) == 2 and parts[1].startswith("http"):
                            urls.append(parts[1])

            return {
                "source": source_name,
                "llms_txt_url": source.llms_txt_url,
                "content": content,
                "parsed_urls": urls,
                "allowed_domains": source.allowed_domains,
            }

        except Exception as e:
            return {
                "source": source_name,
                "error": str(e),
                "llms_txt_url": source.llms_txt_url,
            }

    async def fetch_docs(
        self, url: str, source_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch documentation from a URL with domain security checks.

        Args:
            url: The URL to fetch
            source_names: Optional list of source names to check against their allowed domains.
                         If None, checks against all sources.
        """
        # Determine which sources to check
        sources_to_check = []
        if source_names:
            for name in source_names:
                if name in self.sources:
                    sources_to_check.append(self.sources[name])
        else:
            sources_to_check = list(self.sources.values())

        # Check if URL is allowed by any source
        allowed = False
        matching_sources = []

        for source in sources_to_check:
            if self._is_domain_allowed(url, source.allowed_domains):
                allowed = True
                matching_sources.append(source.name)

        if not allowed:
            return {
                "url": url,
                "error": "Domain not allowed. URL must be from one of the allowed domains from configured sources.",
                "available_sources": [s.name for s in sources_to_check],
                "allowed_domains": [
                    domain for s in sources_to_check for domain in s.allowed_domains
                ],
            }

        try:
            content = await self._fetch_content(url)

            # Basic content parsing - remove excessive whitespace
            cleaned_content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

            return {
                "url": url,
                "content": cleaned_content,
                "content_length": len(content),
                "matching_sources": matching_sources,
                "success": True,
            }

        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "matching_sources": matching_sources,
                "success": False,
            }


# Global manager instance
llms_txt_manager = LLMSTxtManager()


def list_doc_sources() -> List[Dict[str, Any]]:
    """List all available llms.txt documentation sources."""
    return llms_txt_manager.list_sources()


async def fetch_llms_txt_content(source_name: str) -> Dict[str, Any]:
    """Fetch and parse llms.txt content from a specific source."""
    return await llms_txt_manager.fetch_llms_txt(source_name)


async def fetch_documentation(
    url: str, source_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch documentation from a URL with domain security.

    Args:
        url: The documentation URL to fetch
        source_names: Optional list of source names to restrict domain checking

    Returns:
        Dict containing the fetched content or error information
    """
    return await llms_txt_manager.fetch_docs(url, source_names)
