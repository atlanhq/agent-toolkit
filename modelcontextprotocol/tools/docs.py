"""
Documentation tools for MCP server.
Provides only source discovery (llms.txt URLs) for Atlan documentation.

Note: MCP clients should fetch documentation content directly using the
provided URLs. This server intentionally does not proxy or fetch content.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class DocSource:
    """Represents a documentation source with name and llms.txt URL."""

    name: str
    llms_txt_url: str
    allowed_domains: List[str]
    description: str


class DocumentationManager:
    """Manages documentation sources (discovery only)."""

    def __init__(self):
        self.sources: Dict[str, DocSource] = {}
        self._initialize_default_sources()

    def _initialize_default_sources(self):
        """Initialize with default documentation sources."""
        default_sources = [
            DocSource(
                name="Atlan Docs",
                llms_txt_url="https://docs.atlan.com/llms.txt",
                allowed_domains=["docs.atlan.com"],
                description="Official Atlan product documentation",
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
                "description": source.description,
            }
            for source in self.sources.values()
        ]

    # No fetching or validation methods: clients should fetch content directly.


# Global manager instance
documentation_manager = DocumentationManager()


def list_doc_sources() -> List[Dict[str, Any]]:
    """List all available documentation sources with their llms.txt URLs."""
    return documentation_manager.list_sources()
